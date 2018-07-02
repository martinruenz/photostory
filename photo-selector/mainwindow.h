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

#include <QMainWindow>
#include <QJsonObject>
#include <memory>
#include "widget_slide.h"

class QHBoxLayout;
class QFile;
class QProcess;
class QTemporaryFile;

namespace Ui {
class MainWindow;
}

class MainWindow : public QMainWindow{
    Q_OBJECT

public:
    explicit MainWindow(QWidget *parent = 0);
    ~MainWindow();

    size_t countSlides() const;

    SlideWidget* createSlide(SlideWidget::SlideType type = SlideWidget::SlideType::PHOTO);
    SlideWidget* createSlide(const QJsonObject* json, const QString& json_path=QString());
    void addSlide(SlideWidget* slide);
    QJsonObject slideToJson(SlideWidget* slide) const;

    void saveJson(QFile* file) const;
    std::shared_ptr<QTemporaryFile> saveJsonTmp() const;
    bool saveBlend(const QString& blend_path,
                   const QString& output_path=QString(),
                   bool setup_scene=true,
                   bool create_placeholders=false);
    bool renderBlend(const QString& blend_path, const QString& output_path);
    bool openInBlender(); // Not used at the moment
    QString getPythonPhotostoryOp(const QString& json_path,
                                  const QString& output_path=QString(),
                                  bool setup_scene=true,
                                  bool create_placeholders=false) const;

private slots:
    void moveSlide(SlideWidget* obj, int direction);
    void removeSlide(SlideWidget* obj);

    void on_btnAddSlide_clicked();
    void on_btnBlender_clicked();
    void on_btnCompute_clicked();
    void on_btnExport_clicked();
    void on_btnImport_clicked();

    void on_btnAddSlideGPS_clicked();

protected:
    std::shared_ptr<QProcess> startBlender(QStringList arguments = {});
    //    bool waitBlenderStarted(QProcess* process) const;
    bool waitProcessFinished(QProcess* process) const;

private:
    Ui::MainWindow *ui;
    QHBoxLayout* slideLayout;
    std::vector<std::pair<std::shared_ptr<QProcess>, std::shared_ptr<QTemporaryFile>>> process_data; // blender process + json file
};
