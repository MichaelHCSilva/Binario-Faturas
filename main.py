import logging
import os
from applicationVivo import ApplicationVivo

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    
    app = ApplicationVivo()
    app.run()

if __name__ == "__main__":
    main()
