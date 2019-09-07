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
#include <QJsonArray>
#include <QFileDialog>
#include <QJsonDocument>
#include <QProcess>
#include <QTemporaryFile>
#include <QMessageBox>

#include "mainwindow.h"
#include "ui_mainwindow.h"

#include "widget_slide_photo.h"
#include "widget_slide_gps.h"

MainWindow::MainWindow(QWidget *parent) :
    QMainWindow(parent),
    ui(new Ui::MainWindow){
    ui->setupUi(this);
    slideLayout = dynamic_cast<QHBoxLayout*>(ui->areaSlides->layout());

    addSlide(createSlide());
}

MainWindow::~MainWindow(){
    delete ui;
}

size_t MainWindow::countSlides() const{
    int cnt = slideLayout->count();
    if(cnt < 0) throw std::runtime_error("Unexpected return value of QHBoxLayout::count()");
    return size_t(cnt);
}

SlideWidget* MainWindow::createSlide(SlideWidget::SlideType type){
    SlideWidget* widget;
    switch (type) {
    case SlideWidget::SlideType::PHOTO:
        widget = new SlideWidgetPhoto();
        break;
    case SlideWidget::SlideType::GPS:
        widget = new SlideWidgetGPS();
        break;
    }
    widget->setName(QString::number(countSlides()+1));
    return widget;
}

SlideWidget* MainWindow::createSlide(const QJsonObject* json, const QString& json_path){
    SlideWidget* widget;
    QString type = (*json)["type"].toString();
    if(type == "photo_slide") widget = new SlideWidgetPhoto();
    else if(type == "gps_slide") widget = new SlideWidgetGPS();
    else throw std::invalid_argument("Invalid slide type.");
    widget->fromJson(json, json_path);
    return widget;
}

void MainWindow::addSlide(SlideWidget* slide){
    ui->areaSlides->layout()->addWidget(slide);
    slide->setMoveCallback([=](int d) { this->moveSlide(slide, d); });
    slide->setRemoveCallback([=]() { this->removeSlide(slide); });
}

void MainWindow::saveJson(QFile* file) const {
    QJsonArray json_slides;
    for (int i = 0; i < slideLayout->count(); ++i) {
        SlideWidget* slide = dynamic_cast<SlideWidget*>(slideLayout->itemAt(i)->widget());
        json_slides.append(slide->toJson());
    }

    QJsonObject json_root;
    json_root["version"] = "0.1";
    json_root["background"] = ui->cbBackground->currentText();
    json_root["slides"] = json_slides;

    QString content = QJsonDocument(json_root).toJson(QJsonDocument::Indented);
    // std::cout << content.toStdString() << std::endl;

    file->write(content.toUtf8());
}

std::shared_ptr<QTemporaryFile> MainWindow::saveJsonTmp() const {
    auto file = std::make_shared<QTemporaryFile>();
    if (!file->open()) {
        std::cerr << "Could not create temporary json file." << std::endl;
        return nullptr;
    }
    saveJson(file.get());
    file->close();
    return file;
}

bool MainWindow::saveBlend(const QString& blend_path,
                           const QString& output_path,
                           bool setup_scene,
                           bool create_placeholders) {

    // Create temporary json file
    auto file = saveJsonTmp();
    if(file == nullptr)
        return false;

    // Open blender process
    QStringList arguments;
    QString pscript("import bpy; " +
                    getPythonPhotostoryOp(file->fileName(), output_path, setup_scene, create_placeholders) +
                    "bpy.ops.wm.save_as_mainfile(filepath='"+blend_path+"'); bpy.ops.wm.quit_blender();");
    auto process = startBlender(arguments);
    if(!process) return false;
    std::cout << "Generating scene ... ";
    if(!waitProcessFinished(process.get())) return false;
    std::cout << "Saved blender file: " << blend_path.toStdString() << std::endl;
    return true;
}

bool MainWindow::renderBlend(const QString& path, const QString& output_path){
    QStringList arguments;
    arguments << "--background" << path <<  "--render-output" << (output_path+QDir::separator()) << "--render-anim";
    auto process = startBlender(arguments);
    if(!process) return false;
    std::cout << "Rendering ... ";
    if(!waitProcessFinished(process.get())) return false;
    return true;
}

bool MainWindow::openInBlender() {
    // Create temporary json file
    auto file = saveJsonTmp();
    if(file == nullptr){
        std::cout << "failed. Could not create temporary json file." << std::endl;
        return false;
    }

    // Open blender process
    QStringList arguments;
    arguments << "--python-expr" << QString("import bpy; " + getPythonPhotostoryOp(file->fileName()));
    auto process = startBlender(arguments);
    if(!process) return false;
    process_data.push_back({process, file});
    return true;
}

QString MainWindow::getPythonPhotostoryOp(const QString &json_path, const QString &output_path, bool setup_scene, bool create_placeholders) const{
    auto bl = [](bool v) -> QString { return v ? "True" : "False"; };
    QString result;
    if(!output_path.isNull()) result += "bpy.context.scene.render.filepath='"+(output_path+QDir::separator())+"'; ";
    result += "bpy.ops.import_scene.photostory(filepath='"+json_path+"', setup_scene="+bl(setup_scene)+", skip_duplicates="+bl(create_placeholders)+"); ";
    return result;
}

void MainWindow::moveSlide(SlideWidget *obj, int direction){
    int index = slideLayout->indexOf(obj);
    int index_new = index+direction;
    //std::cout << slideLayout->itemAt(0) << std::endl;

    if(index_new<0 || index_new>=slideLayout->count()) return; // Check last / first
    QLayoutItem* item = slideLayout->takeAt(index);
    slideLayout->insertItem(index+direction,item);
}

void MainWindow::removeSlide(SlideWidget *obj){
    slideLayout->removeWidget(obj);
    delete obj;
}

void MainWindow::on_btnAddSlide_clicked(){
    addSlide(createSlide());
}

void MainWindow::on_btnAddSlideGPS_clicked(){
    addSlide(createSlide(SlideWidget::SlideType::GPS));
}

std::shared_ptr<QProcess> MainWindow::startBlender(QStringList arguments) {
    std::cout << "Opening blender ... ";
    std::shared_ptr<QProcess> process = std::make_shared<QProcess>(this);
    // process->setProcessChannelMode(QProcess::ForwardedChannels); // be verbose
    process->start("blender", arguments);
    if(process->waitForStarted()){
        std::cout << "running." << std::endl;
        return process;
    }
    std::cout << "failed. (Can you run 'blender' in terminal?)" << std::endl;
    return nullptr;
}

bool MainWindow::waitProcessFinished(QProcess* process) const {
    if(process->waitForFinished(5e8)){
        std::cout << "done." << std::endl;
        return true;
    }
    std::cout << "failed, an error occured." << std::endl;
    return false;
}

void MainWindow::on_btnBlender_clicked(){
    openInBlender();
}


void MainWindow::on_btnCompute_clicked(){
    QString path = QFileDialog::getExistingDirectory(this, "Render destination");
    if(path.isEmpty()) return;
    QDir dst = QDir(path);
    QString blend_path = dst.absoluteFilePath("generated_scene.blend");
    QString dst_path = dst.absolutePath();

    if(!dst.isEmpty()){
        if(QMessageBox::warning(this, "Directory not empty",
                                "The destination directory is not empty. Do you want to continue?",
                                QMessageBox::StandardButtons(QMessageBox::Yes | QMessageBox::Abort)) == QMessageBox::Abort)
            return;
    }

    // Generate blend file, placeholders for duplicate frames and render
    if(!saveBlend(blend_path, dst_path, true, true)) return;
    if(!renderBlend(blend_path, dst_path)) return;

    // Use script 'generate_duplicates.py' to replace placeholders
    std::cout << "Replaceing placeholders in destination directory ... ";
    QProcess duplicates_process(this);
    QStringList duplicates_arguments;
    duplicates_arguments << "generate_duplicates.py" << "-i" << dst.absoluteFilePath("0001.png") << "-s";
    duplicates_process.start("python3", duplicates_arguments);
    if(!waitProcessFinished(&duplicates_process)) return;

    // Use ffmpeg to generate video
    std::cout << "Executing ffmpeg to generate video ... ";
    QProcess ffmpeg_process(this);
    QStringList ffmpeg_arguments;
    ffmpeg_arguments << "-i" << dst.absoluteFilePath("%04d.png") << "-c:v" << "libx264" << "-crf" << "32" << "-n" << dst.absoluteFilePath("video.mp4");
    ffmpeg_process.start("ffmpeg", ffmpeg_arguments);
    if(!waitProcessFinished(&ffmpeg_process)) return;
}

void MainWindow::on_btnExport_clicked(){
    QString filename = QFileDialog::getSaveFileName(this, "Export as Json", "slides.json", "*.json");
    if(filename.isEmpty()) return;
    QFile f(filename);
    f.open(QIODevice::WriteOnly | QIODevice::Text);
    saveJson(&f);
    f.close();
}

void MainWindow::on_btnImport_clicked(){
    QString filename = QFileDialog::getOpenFileName(this, "Import Json", "slides.json", "*.json");
    if(filename.isEmpty()) return;

    // Load file
    QFile f(filename);
    f.open(QIODevice::ReadOnly | QIODevice::Text);
    QString content = f.readAll();
    f.close();

    // Delete slide iff one empty slide exists (todo)

    // Parse json
    QJsonObject json_root = QJsonDocument::fromJson(content.toUtf8()).object();

    // Load global settings
    for (int i = 0; i < ui->cbBackground->count(); ++i) {
        if(ui->cbBackground->itemText(i) == json_root["background"].toString())
            ui->cbBackground->setCurrentIndex(i);
    }

    // Create slides
    QJsonArray json_slides = json_root["slides"].toArray();
    for(const QJsonValue& slide : json_slides){
        QJsonObject obj = slide.toObject();
        addSlide(createSlide(&obj, filename));
    }
}
