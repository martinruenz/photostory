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

#pragma once

#include <QListWidget>

#include "widget_slide.h"
#include "widget_editlist.h"

class SlideWidgetGPS : public SlideWidget{
    Q_OBJECT

public:
    explicit SlideWidgetGPS(QWidget *parent = nullptr);

    std::vector<QString> getCoordinates() const;
    void addCoordinate(const QString& coord);

    virtual QJsonObject toJson() const;
    virtual void fromJson(const QJsonObject* json, const QString& json_path=QString());

protected:

    EditListWidget gps_coordinates;
};
