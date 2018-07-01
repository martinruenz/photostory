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

#include "slidewidget.h"
#include "ui_slidewidget.h"

SlideWidget::SlideWidget(QWidget *parent) :
    QFrame(parent),
    ui(new Ui::SlideWidget){
    ui->setupUi(this);
}

SlideWidget::~SlideWidget(){
    delete ui;
}

void SlideWidget::setName(const QString &name){
    ui->lName->setText(name);
}

QString SlideWidget::getName() const{
    return ui->lName->text();
}

void SlideWidget::setMoveCallback(const std::function<void (int)>& f){
    connect(ui->btnLeft, &QPushButton::clicked, [=]() {  f(-1); });
    connect(ui->btnRight, &QPushButton::clicked, [=]() {  f(1); });
}
