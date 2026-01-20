# run_client.py
"""
Client Entry Point
Starts the game client.
"""

from client.core.game import Game


def main():
    """Main entry point for client."""
    print("=" * 60)
    print("2D BATTLE ROYALE - GAME CLIENT")
    print("=" * 60)
    
    # Create and run game
    game = Game()
    
    try:
        game.run()
    except KeyboardInterrupt:
        print("\n[Client] Interrupted")
    except Exception as e:
        print(f"[Client] Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("[Client] Goodbye!")


if __name__ == "__main__":
    main()