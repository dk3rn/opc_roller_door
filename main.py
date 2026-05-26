import argparse
import asyncio
import json
import logging
from asyncua import Server, Client, ua
from src.roller_door.roller_door import RolltorApp

ENABLE_LOGGING = True
if ENABLE_LOGGING:
    logging.basicConfig(level=logging.INFO)
else:
    logging.disable(logging.CRITICAL)

_logger = logging.getLogger('asyncua')


class SubHandler:
    def __init__(self, tor: RolltorApp, up_var, down_var):
        self.tor = tor
        self.up_var = up_var
        self.down_var = down_var

    def datachange_notification(self, node, val, data):
        _logger.info("OPC UA data change notification: %r %s", node, val)

        if node == self.up_var:
            self.tor.var_up.set(val)
        elif node == self.down_var:
            self.tor.var_down.set(val)

    def event_notification(self, event):
        _logger.info("OPC UA event notification: %r", event)


class ClientSubHandler:
    def __init__(self, tor: RolltorApp, client: Client, config: dict):
        self.tor = tor
        self.client = client
        self.config = config
        self.node_mapping = {}

    def datachange_notification(self, node, val, data):
        node_id_str = node.nodeid.to_string()
        _logger.info("Client OPC UA data change notification: %s %s", node_id_str, val)
        gui_element_name = self.node_mapping.get(node_id_str)

        if gui_element_name == "Motor_Up":
            self.tor.var_up.set(val)
        elif gui_element_name == "Motor_Down":
            self.tor.var_down.set(val)

    def event_notification(self, event):
        _logger.info("Client OPC UA event notification: %r", event)


async def run_opc_client(tor: RolltorApp):
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
    except Exception as e:
        _logger.error("Configuration Error: %s", e)
        return

    url = config.get("server_url", "opc.tcp://0.0.0.0:4840/th-koeln/opcua/")
    node_config = config.get("nodes", {})

    while tor.running:
        try:
            _logger.info(f"Attempting to connect to Server: {url} ...")
            async with Client(url=url) as client:
                _logger.info("Client connection established successfully!")

                pos_var = client.get_node(node_config.get("Position"))
                error_var = client.get_node(node_config.get("Error"))
                up_var = client.get_node(node_config.get("Motor_Up"))
                down_var = client.get_node(node_config.get("Motor_Down"))
                upper_limit_var = client.get_node(node_config.get("Upper_Limit"))
                lower_limit_var = client.get_node(node_config.get("Lower_Limit"))

                handler = ClientSubHandler(tor, client, config)
                handler.node_mapping = {
                    node_config.get("Motor_Up"): "Motor_Up",
                    node_config.get("Motor_Down"): "Motor_Down"
                }

                sub = await client.create_subscription(500, handler)
                await sub.subscribe_data_change([up_var, down_var])

                _logger.info("Client successfully subscribed to variables.")

                while tor.running:
                    await pos_var.write_value(ua.DataValue(ua.Variant(tor.pos, ua.VariantType.Double)))
                    await error_var.write_value(ua.DataValue(ua.Variant(tor.error, ua.VariantType.Boolean)))
                    await up_var.write_value(ua.DataValue(ua.Variant(tor.var_up.get(), ua.VariantType.Boolean)))
                    await down_var.write_value(ua.DataValue(ua.Variant(tor.var_down.get(), ua.VariantType.Boolean)))
                    await upper_limit_var.write_value(ua.DataValue(ua.Variant(tor.var_upper_limit.get(), ua.VariantType.Boolean)))
                    await lower_limit_var.write_value(ua.DataValue(ua.Variant(tor.var_lower_limit.get(), ua.VariantType.Boolean)))
                    await asyncio.sleep(0.1)

        except Exception as e:
            _logger.error("OPC UA Client Error/Disconnect: %s", e)
            if tor.running:
                _logger.info("Retrying connection in 5 seconds...")
                await asyncio.sleep(5)


async def run_opc_server(tor: RolltorApp):
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/th-koeln/opcua/")
    server.set_server_name("Rolltor OPC UA Server")

    uri = "http://th-koeln.de/ait/opcua/rolltor/"
    idx = await server.register_namespace(uri)

    rolltor_obj = await server.nodes.objects.add_object(idx, "Rolltor")

    pos_var = await rolltor_obj.add_variable(f"ns={idx};s=Position", "Position", 0.0)
    error_var = await rolltor_obj.add_variable(f"ns={idx};s=Error", "Error", False)
    up_var = await rolltor_obj.add_variable(f"ns={idx};s=Motor_Up", "Motor_Up", False)
    down_var = await rolltor_obj.add_variable(f"ns={idx};s=Motor_Down", "Motor_Down", False)
    upper_limit_var = await rolltor_obj.add_variable(f"ns={idx};s=Upper_Limit", "Upper_Limit", False)
    lower_limit_var = await rolltor_obj.add_variable(f"ns={idx};s=Lower_Limit", "Lower_Limit", True)

    await up_var.set_writable()
    await down_var.set_writable()

    handler = SubHandler(tor, up_var, down_var)
    sub = await server.create_subscription(500, handler)
    await sub.subscribe_data_change([up_var, down_var])

    _logger.info("Starting OPC UA Server at %s", server.endpoint.geturl())

    async with server:
        # Loop strictly as long as the UI is running
        while tor.running:
            await pos_var.write_value(tor.pos)
            await error_var.write_value(tor.error)
            await up_var.write_value(tor.var_up.get())
            await down_var.write_value(tor.var_down.get())
            await upper_limit_var.write_value(tor.var_upper_limit.get())
            await lower_limit_var.write_value(tor.var_lower_limit.get())
            await asyncio.sleep(0.1)


async def run_dummy_server():
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/th-koeln/opcua/")
    server.set_server_name("Rolltor OPC UA Dummy Server")

    uri = "http://th-koeln.de/ait/opcua/rolltor/"
    idx = await server.register_namespace(uri)

    rolltor_obj = await server.nodes.objects.add_object(idx, "Rolltor")

    pos_var = await rolltor_obj.add_variable(f"ns={idx};s=Position", "Position", 0.0)
    error_var = await rolltor_obj.add_variable(f"ns={idx};s=Error", "Error", False)
    up_var = await rolltor_obj.add_variable(f"ns={idx};s=Motor_Up", "Motor_Up", False)
    down_var = await rolltor_obj.add_variable(f"ns={idx};s=Motor_Down", "Motor_Down", False)
    upper_limit_var = await rolltor_obj.add_variable(f"ns={idx};s=Upper_Limit", "Upper_Limit", False)
    lower_limit_var = await rolltor_obj.add_variable(f"ns={idx};s=Lower_Limit", "Lower_Limit", True)

    await pos_var.set_writable()
    await error_var.set_writable()
    await up_var.set_writable()
    await down_var.set_writable()
    await upper_limit_var.set_writable()
    await lower_limit_var.set_writable()

    _logger.info("Starting DUMMY OPC UA Server at %s", server.endpoint.geturl())
    async with server:
        while True:
            await asyncio.sleep(1)


async def main():
    parser = argparse.ArgumentParser(description="Rolltor OPC UA Simulation")
    parser.add_argument(
        "-m", "--mode",
        type=str,
        choices=["server", "client", "both"],
        default="both",
        help="Choose whether to run as 'server', 'client', or 'both'."
    )
    args = parser.parse_args()

    # 1. Instanz der RolltorApp (UI) erstellen
    tor = RolltorApp()

    # 2. UI-Loop starten
    task_ui = asyncio.create_task(tor.async_mainloop())

    tasks = []

    if args.mode == "server":
        _logger.info("Running in SERVER mode...")
        task_opc = asyncio.create_task(run_opc_server(tor))
        tasks.append(task_opc)
    elif args.mode == "client":
        _logger.info("Running in CLIENT mode...")
        task_opc = asyncio.create_task(run_opc_client(tor))
        tasks.append(task_opc)
    elif args.mode == "both":
        _logger.info("Running in BOTH mode...")
        task_dummy_server = asyncio.create_task(run_dummy_server())
        # Give the server a moment to start before the client connects
        await asyncio.sleep(1)
        task_client = asyncio.create_task(run_opc_client(tor))
        tasks.append(task_dummy_server)
        tasks.append(task_client)

    # 3. Ausführen, bis das Fenster (UI) geschlossen wird
    await task_ui

    # 4. Tasks abbrechen, wenn das Fenster geschlossen wurde
    _logger.info("UI closed, shutting down remaining tasks...")
    for task in tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    _logger.info("Starting Rolltor application...")

    # asyncio.run() startet den Event-Loop und führt die async main() Funktion aus
    asyncio.run(main())