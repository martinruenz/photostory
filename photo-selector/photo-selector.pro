QT       += core gui

greaterThan(QT_MAJOR_VERSION, 4): QT += widgets

TARGET = photo-selector
TEMPLATE = app

# The following define makes your compiler emit warnings if you use
# any feature of Qt which has been marked as deprecated (the exact warnings
# depend on your compiler). Please consult the documentation of the
# deprecated API in order to know how to port your code away from it.
DEFINES += QT_DEPRECATED_WARNINGS

# You can also make your code fail to compile if you use deprecated APIs.
# In order to do so, uncomment the following line.
# You can also select to disable deprecated APIs only up to a certain version of Qt.
#DEFINES += QT_DISABLE_DEPRECATED_BEFORE=0x060000    # disables all the APIs deprecated before Qt 6.0.0


SOURCES += \
        main.cpp \
        mainwindow.cpp \
    widget_slide.cpp \
    widget_slide_photo.cpp \
    widget_slide_gps.cpp \
    widget_droparea.cpp \
    widget_slidecontainer.cpp \
    widget_editlist.cpp

HEADERS += \
        mainwindow.h \
    widget_slide.h \
    widget_slide_photo.h \
    widget_slide_gps.h \
    widget_droparea.h \
    widget_slidecontainer.h \
    widget_editlist.h

FORMS += \
        mainwindow.ui \
    widget_slide.ui \
    widget_editlist.ui

RESOURCES += \
    resources.qrc
