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

#include "widget_slide_gps.h"
#include "widget_slide.h"
#include "ui_widget_slide.h"

SlideWidgetGPS::SlideWidgetGPS(QWidget *parent) :
    SlideWidget(parent),
    gps_coordinates(parent){

    slide_type = SlideType::GPS;
    ui->verticalLayout->addWidget(&gps_coordinates);
}

std::vector<QString> SlideWidgetGPS::getCoordinates() const{
    std::vector<QString> result = gps_coordinates.getItems();
    return result;
}

void SlideWidgetGPS::addCoordinate(const QString& coord){
    gps_coordinates.addItem(coord);
}

QJsonObject SlideWidgetGPS::toJson() const {
    QJsonObject json = SlideWidget::toJson();
    QJsonArray json_coords;
    std::vector<QString> coordinates = getCoordinates();
    for(QString& c : coordinates) json_coords.append(QJsonValue(c));
    json["type"] = "gps_slide";
    json["gps_coordinates"] = json_coords;
    return json;
}

void SlideWidgetGPS::fromJson(const QJsonObject *json, const QString&) {
    SlideWidget::fromJson(json);
    if(gps_coordinates.count()) throw std::runtime_error("Calling 'fromJson' of non-empty 'SlideWidgetGPS'.");
    QJsonArray coordinates = (*json)["gps_coordinates"].toArray();
    for(const auto& c : coordinates) addCoordinate(c.toString());
}
