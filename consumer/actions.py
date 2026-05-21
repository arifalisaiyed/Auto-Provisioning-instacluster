import logging
import time

logger = logging.getLogger(__name__)

_ACTION_MESSAGES = {
    "restart_server":        "Restarting server {server_id}... [simulated]",
    "clear_temp_files":      "Clearing /tmp on {server_id}... [simulated]",
    "run_hello_world_script": "Running hello_world.sh on {server_id}... [simulated]",
    "scale_up_resources":    "Scaling up resources for {server_id}... [simulated]",
}


def execute_action(server_id: str, action: str) -> None:
    msg_template = _ACTION_MESSAGES.get(action, "Executing {action} on {server_id}... [simulated]")
    msg = msg_template.format(server_id=server_id, action=action)
    logger.info("ACTION EXECUTING: %s", msg)
    time.sleep(2)  # simulate work
    logger.info("ACTION COMPLETE: %s on %s", action, server_id)
