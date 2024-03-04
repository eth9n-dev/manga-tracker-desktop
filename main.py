from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6 import QtGui, QtSql

class Home(QWidget):

    # Constructor
    def __init__(self):
        super().__init__()
        self.initUI()
        self.settings()
        self.clickEvents()
        self.initDB()

    # Objects and Design
    def initUI(self):
        self.home_button = QPushButton("Home")
        self.list_button = QPushButton("My Lists")
        self.create_list_button = QPushButton("Create List")
        self.empty_label = QLabel("")
        self.empty_label2 = QLabel("")

        self.welcome_message = QLabel("MyMangaList allows you to store and track all your manga easily in one place.\nStart tracking your manga now by clicking 'Create List'!",
                                      alignment = Qt.AlignmentFlag.AlignCenter)
        self.welcome_message.setFont(QtGui.QFont("Sanserif"))
        self.welcome_message.setStyleSheet("border: 1px solid black;")

        self.container = QWidget()

        self.master = QHBoxLayout(self.container)

        col1 = QVBoxLayout()
        self.col2 = QVBoxLayout()

        col1.addWidget(self.home_button)
        col1.addWidget(self.list_button)
        col1.addWidget(self.create_list_button)
        col1.addWidget(self.empty_label)

        self.col2.addWidget(self.welcome_message)

        self.master.addLayout(col1, 20)
        self.master.addLayout(self.col2, 80)

        self.setLayout(self.master)
    
    # Create database
    def initDB(self):
        self.db = QtSql.QSqlDatabase.addDatabase('QSQLITE')
        self.db.setDatabaseName('collections.sqlite')

        if not self.db.open():
            raise ConnectionError('Database connection failed.')
        
        query = QtSql.QSqlQuery()

        query.exec("""CREATE TABLE LISTS (
                list_id INTEGER AUTO_INCREMENT,
                list_name TEXT,
                PRIMARY KEY (list_id)
        );""")

        query.exec("""CREATE TABLE MANGA (
                list_id INTEGER,
                manga_name TEXT,
                current_chapter INTEGER,
                url TEXT,
                FOREIGN KEY (list_id) REFERENCES LISTS(list_id)
        );""")

        self.db.close()

    # Window settings
    def settings(self):
        self.setWindowTitle("MyMangaList")
        self.setGeometry(250, 250, 600, 500)

    # Clear view
    def clearView(self):
        for i in reversed(range(self.col2.count())):
            self.col2.itemAt(i).widget().setParent(None)
    
    # Handle button clicks
    def clickEvents(self):
        self.home_button.clicked.connect(self.homePage)
        self.list_button.clicked.connect(self.listPage)
        self.create_list_button.clicked.connect(self.createList)

    # Views
    def homePage(self):
        self.clearView()
        self.col2.addWidget(self.welcome_message)

    def listPage(self):
        self.clearView()
        self.db.open()

        query = QtSql.QSqlQuery()

        query.exec("SELECT list_name, list_id FROM LISTS")
        while (query.next()):
            btn = QPushButton(query.value(0), clicked=lambda checked, arg = query.value(1) : self.viewList(arg))
            self.col2.addWidget(btn)

        self.db.close()
        self.col2.addWidget(self.empty_label2)

    def createList(self):
        name, done = QInputDialog().getText(self, 'Create List', 'Enter the name of your list:')

        if done and name:
            self.db.open()
            
            query = QtSql.QSqlQuery()

            query.exec("SELECT COUNT(*) FROM LISTS")
            
            if (query.next()):
                list_id = query.value(0)
            else:
                list_id = 0

            query.exec(f"""INSERT INTO LISTS (list_id, list_name)
                    VALUES ({list_id}, "{name}")
            ;""")

            self.db.close()
            self.listPage()
        
    def viewList(self, id):
        self.clearView()
        

if __name__ in "__main__":
    app = QApplication([])
    main = Home()
    main.show()
    app.exec()