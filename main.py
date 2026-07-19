from expense_tracker.server import create_server, main as server_main

# Expose the FastMCP instance globally so `fastmcp dev` can find it
mcp = create_server()

if __name__ == "__main__":
    server_main()
