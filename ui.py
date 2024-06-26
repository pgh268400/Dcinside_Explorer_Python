# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'main.ui'
#
# Created by: PyQt5 UI code generator 5.15.6
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(812, 802)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("main.ico"),
                       QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)
        MainWindow.setStyleSheet("QLineEdit {\n"
                                 "    border: 4px solid #3B4890;\n"
                                 "    padding: 4px;\n"
                                 "}\n"
                                 "\n"
                                 "QLineEdit:focus{\n"
                                 "    border: 4px solid rgb(0, 170, 255);\n"
                                 "}\n"
                                 "\n"
                                 "QPushButton {\n"
                                 "    background-color: #3b4890;\n"
                                 "    min-width: 5em;\n"
                                 "    padding: 8px;\n"
                                 "    color:white;\n"
                                 "\n"
                                 "    border-style: outset;\n"
                                 "    border-width: 2px;\n"
                                 "    border-radius : 5px;\n"
                                 "\n"
                                 "    border-color: beige;\n"
                                 "}\n"
                                 "\n"
                                 "QPushButton:pressed {\n"
                                 "   background-color: #29367C;\n"
                                 "    border-style: inset;\n"
                                 "}\n"
                                 "\n"
                                 "QComboBox {\n"
                                 "    border: 4px solid #3B4890;\n"
                                 "    padding: 4px;\n"
                                 "}\n"
                                 "\n"
                                 "QComboBox::drop-down \n"
                                 "{\n"
                                 "    border: 0px;\n"
                                 "}\n"
                                 "\n"
                                 "QComboBox::down-arrow {\n"
                                 "    image: url(git.png);\n"
                                 "    width: 28px;\n"
                                 "    height: 28px;\n"
                                 "}")
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSizeConstraint(
            QtWidgets.QLayout.SetDefaultConstraint)
        self.horizontalLayout.setSpacing(2)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.comboBox = QtWidgets.QComboBox(self.centralwidget)
        font = QtGui.QFont()
        font.setFamily("맑은 고딕")
        font.setPointSize(10)
        self.comboBox.setFont(font)
        self.comboBox.setObjectName("comboBox")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.horizontalLayout.addWidget(self.comboBox)
        self.txt_repeat = QtWidgets.QLineEdit(self.centralwidget)
        font = QtGui.QFont()
        font.setFamily("맑은 고딕")
        font.setPointSize(10)
        self.txt_repeat.setFont(font)
        self.txt_repeat.setToolTip("")
        self.txt_repeat.setStyleSheet("#searchBox {\n"
                                      "    border: 4px solid #3b4890;\n"
                                      "}")
        self.txt_repeat.setObjectName("txt_repeat")
        self.horizontalLayout.addWidget(self.txt_repeat)
        self.txt_id = QtWidgets.QLineEdit(self.centralwidget)
        font = QtGui.QFont()
        font.setFamily("맑은 고딕")
        font.setPointSize(10)
        self.txt_id.setFont(font)
        self.txt_id.setToolTip("")
        self.txt_id.setStyleSheet("#searchBox {\n"
                                  "    border: 4px solid #3b4890;\n"
                                  "}")
        self.txt_id.setObjectName("txt_id")
        self.horizontalLayout.addWidget(self.txt_id)
        self.txt_keyword = QtWidgets.QLineEdit(self.centralwidget)
        font = QtGui.QFont()
        font.setFamily("맑은 고딕")
        font.setPointSize(10)
        self.txt_keyword.setFont(font)
        self.txt_keyword.setStyleSheet("")
        self.txt_keyword.setObjectName("txt_keyword")
        self.horizontalLayout.addWidget(self.txt_keyword)
        self.btn_Search = QtWidgets.QPushButton(self.centralwidget)
        font = QtGui.QFont()
        font.setFamily("나눔고딕")
        font.setBold(False)
        font.setWeight(50)
        self.btn_Search.setFont(font)
        self.btn_Search.setObjectName("btn_Search")
        self.horizontalLayout.addWidget(self.btn_Search)
        self.horizontalLayout.setStretch(0, 3)
        self.horizontalLayout.setStretch(1, 2)
        self.horizontalLayout.setStretch(2, 3)
        self.horizontalLayout.setStretch(3, 10)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.articleView = QtWidgets.QTableWidget(self.centralwidget)
        self.articleView.setStyleSheet("QLabel#label{\n"
                                       "color : rgb(85, 85, 255)\n"
                                       "}")
        self.articleView.setShowGrid(True)
        self.articleView.setGridStyle(QtCore.Qt.SolidLine)
        self.articleView.setObjectName("articleView")
        self.articleView.setColumnCount(7)
        self.articleView.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.articleView.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.articleView.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.articleView.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.articleView.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.articleView.setHorizontalHeaderItem(4, item)
        item = QtWidgets.QTableWidgetItem()
        self.articleView.setHorizontalHeaderItem(5, item)
        item = QtWidgets.QTableWidgetItem()
        self.articleView.setHorizontalHeaderItem(6, item)
        self.verticalLayout.addWidget(self.articleView)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label = QtWidgets.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setFamily("나눔고딕")
        font.setBold(True)
        font.setItalic(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setStyleSheet("QLabel#label{\n"
                                 "color : rgb(85, 85, 255)\n"
                                 "}")
        self.label.setObjectName("label")
        self.horizontalLayout_2.addWidget(self.label)
        self.txt_status = QtWidgets.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setFamily("나눔고딕")
        font.setPointSize(10)
        self.txt_status.setFont(font)
        self.txt_status.setAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.txt_status.setObjectName("txt_status")
        self.horizontalLayout_2.addWidget(self.txt_status)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        self.btn_Search.clicked.connect(MainWindow.search)  # type: ignore
        self.articleView.itemDoubleClicked['QTableWidgetItem*'].connect(
            MainWindow.item_dbl_click)  # type: ignore
        self.txt_keyword.returnPressed.connect(
            MainWindow.search)  # type: ignore
        self.txt_id.returnPressed.connect(MainWindow.search)  # type: ignore
        self.txt_repeat.returnPressed.connect(
            MainWindow.search)  # type: ignore
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate(
            "MainWindow", "DCINSIDE ARTICLE FINDER v0.152 Beta"))
        self.comboBox.setItemText(0, _translate("MainWindow", "제목+내용"))
        self.comboBox.setItemText(1, _translate("MainWindow", "제목"))
        self.comboBox.setItemText(2, _translate("MainWindow", "내용"))
        self.comboBox.setItemText(3, _translate("MainWindow", "글쓴이"))
        self.comboBox.setItemText(4, _translate("MainWindow", "댓글"))
        self.txt_repeat.setPlaceholderText(_translate("MainWindow", "탐색 횟수"))
        self.txt_id.setPlaceholderText(_translate("MainWindow", "갤러리 ID"))
        self.txt_keyword.setPlaceholderText(_translate("MainWindow", "검색어"))
        self.btn_Search.setText(_translate("MainWindow", "검색"))
        self.articleView.setSortingEnabled(True)
        item = self.articleView.horizontalHeaderItem(0)
        item.setText(_translate("MainWindow", "번호"))
        item = self.articleView.horizontalHeaderItem(1)
        item.setText(_translate("MainWindow", "제목"))
        item = self.articleView.horizontalHeaderItem(2)
        item.setText(_translate("MainWindow", "댓글수"))
        item = self.articleView.horizontalHeaderItem(3)
        item.setText(_translate("MainWindow", "글쓴이"))
        item = self.articleView.horizontalHeaderItem(4)
        item.setText(_translate("MainWindow", "작성일"))
        item = self.articleView.horizontalHeaderItem(5)
        item.setText(_translate("MainWindow", "조회"))
        item = self.articleView.horizontalHeaderItem(6)
        item.setText(_translate("MainWindow", "추천"))
        self.label.setText(_translate(
            "MainWindow", "Copyright 2022. File(pgh268400@naver.com) all rights reserved."))
        self.txt_status.setText(_translate("MainWindow", "상태 : IDLE"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
