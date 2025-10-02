import sys
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from mainwindow import MainWindow

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('app.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
 

    try:
        app.setWindowIcon(QIcon('../icon.png'))
    except:
        pass
    
    window = MainWindow()
    window.show()

    logging.info("Приложение 'Крошка Картошка' запущено")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()