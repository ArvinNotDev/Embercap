"""Embercap entry point. Run from any directory with Python 3.11+."""
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'

def main():
    import argparse
    parser=argparse.ArgumentParser(description='Embercap: The Fifteen Lanterns')
    parser.add_argument('--smoke',type=int,metavar='FRAMES',help='Render a bounded number of frames for startup checks')
    args=parser.parse_args()
    from src.game import Game
    Game().run(max_frames=args.smoke)

if __name__=='__main__': main()
