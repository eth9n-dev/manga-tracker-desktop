import requests, string, webbrowser, uuid, asyncio

from update_check import isUpToDate
from PyQt6.QtWidgets import QPushButton, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QInputDialog, QScrollArea, QMessageBox, QApplication
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

        asyncio.run(self.checkForUpdate())

    # Objects and Design
    def initUI(self):
        self.home_button = QPushButton("Home")
        self.list_button = QPushButton("My Lists")
        self.create_list_button = QPushButton("Create List")
        self.add_manga_button = QPushButton("Add Manga")
        self.gif_label = QLabel()
        gif = QtGui.QMovie('_internal/mascot.gif')
        self.gif_label.setMovie(gif)
        self.gif_label.setScaledContents(True)
        self.gif_label.setMaximumSize(125, 159)
        gif.start()
        self.empty_label = QLabel("")
        self.empty_label2 = QLabel("")
        self.empty_label3 = QLabel("")
        logoImage = QtGui.QPixmap("_internal/logo.png")
        self.logo = QLabel(alignment = Qt.AlignmentFlag.AlignCenter)
        self.logo.setPixmap(logoImage)

        self.welcome_message = QLabel("MyMangaList allows you to store and track all your manga easily in one place.\nStart tracking your manga now by clicking 'Create List'!",
                                      alignment = Qt.AlignmentFlag.AlignCenter)
        self.welcome_message.setFont(QtGui.QFont("Sanserif"))

        self.container = QWidget()
        self.master = QHBoxLayout(self.container)

        col1 = QVBoxLayout()
        self.col2 = QVBoxLayout()

        # Side Bar
        col1.addWidget(self.home_button)
        col1.addWidget(self.list_button)
        col1.addWidget(self.create_list_button)
        col1.addWidget(self.add_manga_button)
        col1.addWidget(self.empty_label)
        col1.addWidget(self.gif_label)

        # Main View
        self.col2.addWidget(self.empty_label2)
        self.col2.addWidget(self.logo)
        self.col2.addWidget(self.welcome_message)
        self.col2.addWidget(self.empty_label3)
 
        # App Layout
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
                cover_data TEXT,
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
        self.add_manga_button.clicked.connect(self.addManga)

    # Home page view
    def homePage(self):
        self.clearView()

        self.col2.addWidget(self.empty_label2)
        self.col2.addWidget(self.logo)
        self.col2.addWidget(self.welcome_message)
        self.col2.addWidget(self.empty_label3)

    # List page view
    def listPage(self):
        self.clearView()
        self.db.open()

        query = QtSql.QSqlQuery()

        query.exec("SELECT list_name, list_id FROM LISTS")
        while (query.next()):
            btn = QPushButton(query.value(0), clicked = lambda checked, arg = query.value(1) : self.viewList(arg))
            self.col2.addWidget(btn)

        self.db.close()
        self.col2.addWidget(self.empty_label2)

    # Create list functionality
    def createList(self):
        name, done = QInputDialog().getText(self, 'Create List', 'Enter the name of your list:')

        if done and name:
            self.db.open()
            
            query = QtSql.QSqlQuery()
            query.exec("SELECT COUNT(*) FROM LISTS")
            
            if (query.next()):
                list_id = uuid.uuid4().int>>64
            else:
                list_id = 0

            query.exec(f"""INSERT INTO LISTS (list_id, list_name)
                    VALUES ({list_id}, "{name}")
                    ;""")

            self.db.close()
            self.listPage()
    
    # View specific list
    def viewList(self, id):
        self.db.open()
        self.clearView()
        
        query = QtSql.QSqlQuery()
        query.exec(f"SELECT * FROM MANGA WHERE list_id = {id}")

        container = QWidget()
        contentBox = QVBoxLayout()
        contentBox.setAlignment(Qt.AlignmentFlag.AlignTop)
        scrollArea = QScrollArea()

        container.setLayout(contentBox)
        scrollArea.setWidget(container)
        scrollArea.setWidgetResizable(True)

        deleteButton = QPushButton("Delete this List", clicked = lambda checked, arg = id : self.deleteList(arg))
        deleteButton.setStyleSheet("background-color: #f44336;")

        while (query.next()):
            card = QWidget()
            card.setMaximumHeight(150)
            button = QPushButton(query.value(1), clicked = lambda checked, arg = query.value(3) : self.openLink(arg))
            button2 = QPushButton("Update Current Chapter", clicked = lambda checked, arg = query.value(0), arg2 = query.value(1) : self.editChapterNumber(arg, arg2))
            button3 = QPushButton("Delete Manga", clicked = lambda checked, arg = query.value(0), arg2 = query.value(1) : self.deleteEntry(arg, arg2))
            button3.setStyleSheet("background-color: #f44336; border-radius: 8px")
            chapterNum = QLabel(f"Current Chapter: {query.value(2)}")
            chapterNum.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chapterNum.setFont(QtGui.QFont('Sanserif', 15))
            
            r = requests.get(query.value(4))
            
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(r.content)
            
            image = QLabel()
            image.setPixmap(pixmap)
            image.setScaledContents(True)
            image.setMaximumSize(100, 150)
            
            layout = QHBoxLayout()
            col1 = QVBoxLayout()
            col2 = QVBoxLayout()
            col2.setAlignment(Qt.AlignmentFlag.AlignTop)
            
            layout.addLayout(col1)
            layout.addLayout(col2)
            
            col1.addWidget(image)
            col2.addWidget(button, 25)
            col2.addWidget(chapterNum, 50)
            col2.addWidget(button2, 12)
            col2.addWidget(button3, 12)
            
            card.setLayout(layout)
            contentBox.addWidget(card)
        
        self.col2.addWidget(scrollArea)
        self.col2.addWidget(deleteButton)
        self.db.close()
        
    # Add manga to list functionality
    def addManga(self):
        # Create dialog for input
        dialog = QInputDialog()
        dialog.setWindowTitle("Add Manga")
        self.db.open()
        
        url, done = dialog.getText(self, 'Add Manga', 'Manga URL:')

        if url and done:
            # Check for valid URL
            if "manhwatop.com/manga/" not in url:
                messageBox = QMessageBox(QMessageBox.Icon.Warning, "Invalid Input", "The url entered was not a valid manhwatop.com link.", QMessageBox.StandardButton.Ok)
                messageBox.exec()
                return

            title = self.getTitle(url)
            cover = self.getCover(title)

            # Ensure we don't add invalid data
            if cover == None:
                return
            
            # Dialog to know what list to add to
            dialog2 = QInputDialog()
            dialog2.setWindowTitle("Add Manga")

            # Get a list of all manga lists
            query = QtSql.QSqlQuery()
            query.exec("SELECT list_name FROM LISTS")

            items = []

            while (query.next()):
                items.append(query.value(0))

            listName, done = dialog2.getItem(self, 'Add Manga', 'Choose a List:', items)

            if listName and done:
                # Find ID based on list name
                query.exec(f"SELECT list_id FROM LISTS WHERE list_name = '{listName}'")
                
                while (query.next()):
                    listId = query.value(0)

                query.exec(f'INSERT INTO MANGA (`list_id`, `manga_name`, `current_chapter`, `url`, `cover_data`) VALUES ({listId}, "{title}", 0, "{url}", "{cover}")')
                self.viewList(listId)

        self.db.close()

    # Strip and prepare title for db
    def getTitle(self, url : str):
        title = url.split('/')[-2]
        title = title.replace('-', ' ')
        
        stopwords = ['series', 'comic', 'manhwa']
        title = title.split()
        resultwords = [word for word in title if word.lower() not in stopwords]
        result = ' '.join(resultwords)

        return string.capwords(result)

    # Retrieve cover art through mangadex api
    def getCover(self, title):
        base_url = "https://api.mangadex.org"

        # Get MangaID
        r = requests.get(
            f"{base_url}/manga",
            params={"title": title}
        )

        if (r.status_code == 404 or r.status_code == 503):
            messageBox = QMessageBox(QMessageBox.Icon.Warning, "API Warning", "The MangaDex API is currently down, try again later.", QMessageBox.StandardButton.Ok)
            messageBox.exec()
            return None

        j = r.json()
        id = j['data'][0]['id']

        # Get CoverID
        r2 = requests.get(f"{base_url}/manga/{id}?includes[]=cover_art")
        
        j2 = r2.json()
        for i in j2['data']['relationships']:
            if i['type'] == 'cover_art':
                coverId = i['attributes']['fileName']

        return (f"https://uploads.mangadex.org/covers/{id}/{coverId}.256.jpg")
    
    # Edit chapter number in db
    def editChapterNumber(self, id : int, title : str):
        dialog = QInputDialog()
        dialog.setWindowTitle("Edit Chapter Number")
        self.db.open()

        newChapter, done = dialog.getInt(self, "Edit Chapter Number", "Chapter Number:")

        if newChapter and done:
            query = QtSql.QSqlQuery()
            query.exec(f"UPDATE MANGA SET current_chapter = {newChapter} WHERE manga_name = '{title}' AND list_id = {id}")
        
        self.db.close()
        self.viewList(id)

    # Delete manga in db
    def deleteEntry(self, id, title):
        messageBox = QMessageBox(QMessageBox.Icon.Warning, "Delete Manga", "Are you sure you want to delete this manga?")
        messageBox.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        messageBox.setDefaultButton(QMessageBox.StandardButton.Cancel)
        self.db.open()
        
        value = messageBox.exec()

        if value == QMessageBox.StandardButton.Yes:
            query = QtSql.QSqlQuery()
            query.exec(f"DELETE FROM MANGA WHERE manga_name = '{title}' AND list_id = {id}")

        self.db.close()
        self.viewList(id)

    # Delete list in db
    def deleteList(self, id):
        self.db.open()

        messageBox = QMessageBox(QMessageBox.Icon.Warning, "Delete List", "Are you sure you want to delete this list?")
        messageBox.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        messageBox.setDefaultButton(QMessageBox.StandardButton.Cancel)
        
        if messageBox.exec() == QMessageBox.StandardButton.Yes:
            query = QtSql.QSqlQuery()
            query.exec(f"DELETE FROM LISTS WHERE list_id = {id}")

        self.listPage()
        self.db.close()

    # Open manga website
    def openLink(self, url):
        webbrowser.open(url)

    # Check for updates
    async def checkForUpdate(self):
        if isUpToDate('_internal/main.py', 'https://raw.githubusercontent.com/eth9n-dev/manga-tracker-desktop/main/main.py') == False:
            await asyncio.sleep(0.1)
            
            messageBox = QMessageBox(QMessageBox.Icon.Information, "Update Available", "A new update is available, get it <a href='https://github.com/eth9n-dev/manga-tracker-desktop/releases'>here</a>")
            messageBox.setStandardButtons(QMessageBox.StandardButton.Ok)
            messageBox.exec()


if __name__ in "__main__":
    app = QApplication([])
    main = Home()
    main.show()
    app.exec()