cmake_minimum_required(VERSION 3.1)
project(photo-selector)

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_INCLUDE_CURRENT_DIR ON)
find_package(Qt5 REQUIRED Core Gui Widgets)

include_directories(. ${QT_INCLUDES})

set(SOURCES
  main.cpp
  mainwindow.cpp
  widget_slide.cpp
  widget_slide_photo.cpp
  widget_slide_gps.cpp
  widget_droparea.cpp
  widget_slidecontainer.cpp
  widget_editlist.cpp
)

set(FORMS
  mainwindow.ui
  widget_slide.ui
  widget_editlist.ui
)

# Optionally, use ffmpegthumbnailer
set(FFMPEGTHUMBNAILER_DIR "${CMAKE_CURRENT_SOURCE_DIR}/third_party/ffmpegthumbnailer")
if(EXISTS "${FFMPEGTHUMBNAILER_DIR}/build/libffmpegthumbnailer.so")
    message("Using ffmpegthumbnailer")
    include_directories(${FFMPEGTHUMBNAILER_DIR}/libffmpegthumbnailer)
    add_definitions(-DWITH_FFMPEGTHUMBNAILER)
    set(LIBRARIES ${LIBRARIES} ${FFMPEGTHUMBNAILER_DIR}/build/libffmpegthumbnailer.so)
endif()

get_property(dirs DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR} PROPERTY INCLUDE_DIRECTORIES)
foreach(dir ${dirs})
  message(STATUS "dir='${dir}'")
endforeach()

qt5_wrap_ui(HEADERS_UI ${FORMS})
add_executable(${PROJECT_NAME} ${SOURCES} ${HEADERS_UI} resources.qrc)
target_link_libraries(${PROJECT_NAME} ${LIBRARIES})
qt5_use_modules(${PROJECT_NAME} Widgets)
