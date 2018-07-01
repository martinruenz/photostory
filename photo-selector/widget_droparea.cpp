// ====================================================================
// Copyright 2018 by Martin Rünz <contact@martinruenz.de>
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>
// ====================================================================

#include <iostream>
#include <QDragEnterEvent>
#include <QMimeData>
#include <QHBoxLayout>
#include <QFileInfo>

#include "widget_droparea.h"

#ifdef WITH_FFMPEGTHUMBNAILER
#include "videothumbnailer.h"
#include "stringoperations.h"
#include "filmstripfilter.h"
#endif

DropArea::DropArea(QWidget *parent, const std::vector<QString>& extensions) : QListWidget(parent) {
    setAcceptDrops(true);
    setAutoFillBackground(true);

    setLayoutMode(LayoutMode::Batched);
    setTextElideMode(Qt::TextElideMode::ElideLeft);
    setViewMode(ViewMode::IconMode);
    setIconSize(QSize(175,175));
    setUniformItemSizes(true);
    setFlow(Flow::LeftToRight);

    addValidExtensions(extensions);

//    setObjectName("droparea");


//    QHBoxLayout* hbox = new QHBoxLayout(this);
//    labelDropzone = new QLabel(this);
//    hbox->addStretch();
//    hbox->addWidget(labelDropzone);
//    hbox->addStretch();
//    labelDropzone->setText("<Drag & Drop images here>");
//    labelDropzone->setAlignment(Qt::AlignCenter);
//    labelDropzone->setPixmap(QPixmap(":/assets/icon_images.svg").scaled(100,100));
//    labelDropzone->setAcceptDrops(true);

}

QImage DropArea::getThumbnail(const QString &path) {
    const int thumb_size = 175;
    QImage thumb(path);
    if(!thumb.isNull()){
        return thumb.scaled(thumb_size, thumb_size, Qt::AspectRatioMode::KeepAspectRatio, Qt::TransformationMode::FastTransformation);
    } else {
#ifdef WITH_FFMPEGTHUMBNAILER
        ffmpegthumbnailer::VideoThumbnailer videoThumbnailer(thumb_size, true, true, 8, true);

        // add strip
        ffmpegthumbnailer::FilmStripFilter* filmStripFilter = new ffmpegthumbnailer::FilmStripFilter();
        videoThumbnailer.addFilter(filmStripFilter);

        // extract
        std::vector<uint8_t> buff;
        ffmpegthumbnailer::VideoFrameInfo info =  videoThumbnailer.generateThumbnail(path.toStdString(), Rgb, buff);

        // clean, convert, return
        delete filmStripFilter;
        return QImage(buff.data(), info.width, info.height, info.width * 3, QImage::Format_RGB888);
#endif
    }

    return QImage(":/assets/icon_no_thumb.png");
}

void DropArea::addValidExtensions(const std::vector<QString> &extensions){
    for(const QString& e : extensions)
        valid_extensions.push_back(e.toLower());
}

bool DropArea::isValidFile(const QString &path) const{
    QString path_lower = path.toLower();
    for(const QString& e : valid_extensions){
        if(path_lower.endsWith(e)) return true;
    }
    return false;
}

void DropArea::addPath(const QString &path){

    if(!isValidFile(path)) {
        std::cout << "Unsupported file type: " << path.toStdString() << std::endl;
        return;
    }

    //image.pixelFormat()
    //QIcon(QPixmap::fromImage(image))

    QListWidgetItem* item = new QListWidgetItem(QIcon(QPixmap::fromImage(getThumbnail(path))), path);
    item->setSizeHint(QSize(200,200));
    addItem(item);
    setStyleSheet("background-image: url(:/);");
}

std::vector<QString> DropArea::getPaths() const{
    std::vector<QString> result;
    int cnt = count();
    result.reserve(cnt);
    for (int i = 0; i < cnt; ++i) result.push_back((item(i)->text()));
    return result;
}

void DropArea::dragEnterEvent(QDragEnterEvent *event){
    //setBackgroundRole(QPalette::Highlight);
    updateBackground(true);
    event->acceptProposedAction();
    //emit changed(event->mimeData());
}

void DropArea::dragMoveEvent(QDragMoveEvent *event){
    event->acceptProposedAction();
}

void DropArea::dropEvent(QDropEvent *event){
    const QMimeData *mimeData = event->mimeData();

    QList<QUrl> urlList = mimeData->urls();
    for (int i = 0; i < urlList.size(); ++i)
        addPath(urlList.at(i).toLocalFile());

    //setBackgroundRole(QPalette::Dark);
    updateBackground(false);
    event->acceptProposedAction();
}

void DropArea::updateBackground(bool highlight){
    if(count()>0) return;
    if(highlight){
        setStyleSheet("background-image: url(:/assets/icon_images_hover.svg);");
    } else {
        setStyleSheet("background-image: url(:/assets/icon_images.svg);");
    }
}

void DropArea::dragLeaveEvent(QDragLeaveEvent *event){
    //setBackgroundRole(QPalette::Dark);
    updateBackground(false);
    event->accept();
}


//void DropArea::clear()
//{
//    setText(tr("<drop content>"));
//    setBackgroundRole(QPalette::Dark);

//    //emit changed();
//}
