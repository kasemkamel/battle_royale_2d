# run_server.py
"""
Server Entry Point
Starts the game server.
"""

import asyncio
import signal
import sys
from server.core.server import GameServer


def signal_handler(server):
    """Handle graceful shutdown on CTRL+C."""
    def handler(sig, frame):
        print("\n[Server] Shutdown signal received...")
        asyncio.create_task(server.shutdown())
    return handler


def main():
    """Main entry point for server."""
    print("=" * 60)
    print("2D BATTLE ROYALE - GAME SERVER")
    print("=" * 60)
    
    # Create server
    server = GameServer()
    
    # Set up signal handling for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler(server))
    
    # Run server
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("\n[Server] Interrupted")
    except Exception as e:
        print(f"[Server] Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        server.stop()
        print("[Server] Goodbye!")


if __name__ == "__main__":
    main()