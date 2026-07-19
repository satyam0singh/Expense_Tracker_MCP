from locust import HttpUser, task, between
import json

class MCPUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def test_list_tools(self):
        # In a real MCP SSE/HTTP setup, there is an endpoint for POSTing messages.
        # FastMCP implements an SSE transport. This simulates sending a JSON-RPC 
        # request for tools/list.
        
        # Note: Actual MCP via HTTP involves establishing an SSE connection first
        # and then POSTing to the returned message endpoint. This is a simplified
        # mock representation of the POST action for latency benchmarking.
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 1
        }
        self.client.post("/messages", json=payload, name="List Tools")

    @task(1)
    def test_call_tool(self):
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "get_expenses",
                "arguments": {}
            },
            "id": 2
        }
        self.client.post("/messages", json=payload, name="Call get_expenses")
