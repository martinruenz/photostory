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
#include <QLabel>

class DropArea : public QListWidget{
    Q_OBJECT
public:
    explicit DropArea(QWidget *parent, const std::vector<QString>& extensions);

    static QImage getThumbnail(const QString& path);

    void addValidExtensions(const std::vector<QString>& extensions);
    bool isValidFile(const QString& path) const;
    void addPath(const QString& path);
    std::vector<QString> getPaths() const;

    void dragEnterEvent(QDragEnterEvent *event) override;
    void dragMoveEvent(QDragMoveEvent *event) override;
    void dragLeaveEvent(QDragLeaveEvent *event) override;
    void dropEvent(QDropEvent *event) override;

    void updateBackground(bool highlight);

signals:

public slots:

private:

    std::vector<QString> valid_extensions;
    //QLabel* labelDropzone;
};
