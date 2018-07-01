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

#include "widget_editlist.h"
#include "ui_widget_editlist.h"

#include <QListWidgetItem>

EditListWidget::EditListWidget(QWidget *parent) :
    QWidget(parent),
    ui(new Ui::EditListWidget){
    ui->setupUi(this);

    connect(ui->btn_plus, &QPushButton::clicked, [this](){ this->addItem("<Lat>, <Long>"); });
    connect(ui->btn_minus, &QPushButton::clicked, [&]() {
        QList<QListWidgetItem*> selected_items = ui->list->selectedItems();
        for(auto& r : selected_items){
            ui->list->removeItemWidget(r);
            delete r;
        }
    });

    connect(ui->btn_up, &QPushButton::clicked, [&]() {
        int row = ui->list->currentRow();
        if(row < 1) return;
        QListWidgetItem* item = ui->list->takeItem(row);
        ui->list->insertItem(row - 1, item);
        ui->list->setCurrentRow(row - 1);
    });

    connect(ui->btn_down, &QPushButton::clicked, [&]() {
        int row = ui->list->currentRow();
        if(row >= ui->list->count() || row < 0) return;
        QListWidgetItem* item = ui->list->takeItem(row);
        ui->list->insertItem(row + 1, item);
        ui->list->setCurrentRow(row + 1);
    });
}

EditListWidget::~EditListWidget(){
    delete ui;
}

std::vector<QString> EditListWidget::getItems() const {
    std::vector<QString> result;
    for(int r = 0; r < ui->list->count(); r++)
        result.push_back(ui->list->item(r)->text());

    return result;
}

void EditListWidget::addItem(const QString &value){
    ui->list->addItem(value);
    QListWidgetItem* item = ui->list->item(ui->list->count()-1);
    item->setFlags(item->flags() | Qt::ItemIsEditable);
}

unsigned EditListWidget::count() const{
    ui->list->count();
}
