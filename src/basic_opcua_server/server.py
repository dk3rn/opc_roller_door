import asyncio
import logging
from asyncua import Server, ua
from roller_door.roller_door import RolltorApp

ENABLE_LOGGING = True
if ENABLE_LOGGING:
    logging.basicConfig(level=logging.INFO)
else:
    logging.disable(logging.CRITICAL)

_logger = logging.getLogger('asyncua')

class SubHandler:
    def datachange_notification(self, node, val, data):
        _logger.info("OPC UA data change notification: %r %s", node, val)
        node_id = node.nodeid.Identifier
        if "Motor_Up" in node_id:
            tor.var_up.set(val)
        elif "Motor_Down" in node_id:
            tor.var_down.set(val)

    def event_notification(self, event):
        _logger.info("OPC UA event notification: %r", event)


async def run_opc_server(tor: RolltorApp):
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/th-koeln/opcua/")
    server.set_server_name("Rolltor OPC UA Server")

    uri = "http://th-koeln.de/ait/opcua/rolltor/"
    idx = await server.register_namespace(uri)

    rolltor_obj = await server.nodes.objects.add_object(idx, "Rolltor")

    pos_var = await rolltor_obj.add_variable(idx, "Position", 0.0)
    error_var = await rolltor_obj.add_variable(idx, "Error", False)
    up_var = await rolltor_obj.add_variable(idx, "Motor_Up", False)
    down_var = await rolltor_obj.add_variable(idx, "Motor_Down", False)
    upper_limit_var = await rolltor_obj.add_variable(idx, "Upper_Limit", False)
    lower_limit_var = await rolltor_obj.add_variable(idx, "Lower_Limit", True)

    await up_var.set_writable()
    await down_var.set_writable()

    handler = SubHandler()
    sub = await server.create_subscription(500, handler)
    await sub.subscribe_data_change([up_var, down_var])

    _logger.info("Starting OPC UA Server at %s", server.endpoint.geturl())

    async with server:
        while tor.running:
            await pos_var.write_value(tor.pos)
            await error_var.write_value(tor.error)
            await up_var.write_value(tor.var_up.get())
            await down_var.write_value(tor.var_down.get())
            await upper_limit_var.write_value(tor.var_upper_limit.get())
            await lower_limit_var.write_value(tor.var_lower_limit.get())
            await asyncio.sleep(0.1)

if __name__ == "__main__":
    _logger.info("This script is not meant to be run directly. Run main.py instead.")
