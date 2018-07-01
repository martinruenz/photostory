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

#include <QJsonDocument>
#include <QJsonArray>
#include <QJsonObject>

#include "widget_slide.h"
#include "widget_slide_photo.h"
#include "ui_widget_slide.h"

const std::vector<QString> SlideWidgetPhoto::supported_extensions = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".jp2", ".j2c", ".exr", ".tga",
                                                                     ".mp4", ".avi", ".mpg", ".mpeg", ".dvd", ".vob", ".mov", ".ogg", ".ogv", ".dv", ".mkv"};

SlideWidgetPhoto::SlideWidgetPhoto(QWidget *parent) :
    SlideWidget(parent),
    foreground_area(parent, supported_extensions),
    background_area(parent, supported_extensions){

    slide_type = SlideType::PHOTO;
    ui->verticalLayout->addWidget(&foreground_area);
    ui->verticalLayout->addWidget(&background_area);
}

std::vector<QString> SlideWidgetPhoto::getForegroundPaths() const{
    return foreground_area.getPaths();
}

std::vector<QString> SlideWidgetPhoto::getBackgroundPaths() const{
    return background_area.getPaths();
}

void SlideWidgetPhoto::addForegroundPath(const QString &path){
    foreground_area.addPath(path);
}

void SlideWidgetPhoto::addBackgroundPath(const QString &path){
    background_area.addPath(path);
}

QJsonObject SlideWidgetPhoto::toJson() const {
    QJsonObject json = SlideWidget::toJson();
    QJsonArray json_fpaths, json_bpaths;
    std::vector<QString> fpaths = getForegroundPaths();
    std::vector<QString> bpaths = getBackgroundPaths();
    for(QString& p : fpaths) json_fpaths.append(QJsonValue(p));
    for(QString& p : bpaths) json_bpaths.append(QJsonValue(p));
    json["type"] = "photo_slide";
    json["foreground_paths"] = json_fpaths;
    json["background_paths"] = json_bpaths;
    return json;
}

void SlideWidgetPhoto::fromJson(const QJsonObject *json) {
    SlideWidget::fromJson(json);
    if(foreground_area.count() || background_area.count()) throw std::runtime_error("Calling 'fromJson' of non-empty 'SlideWidgetPhoto'.");

    QJsonArray jsonFgPaths = (*json)["foreground_paths"].toArray();
    QJsonArray jsonBgPaths = (*json)["background_paths"].toArray();
    for(const auto& p : jsonFgPaths) addForegroundPath(p.toString());
    for(const auto& p : jsonBgPaths) addBackgroundPath(p.toString());
}
