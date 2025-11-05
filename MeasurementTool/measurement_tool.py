from PySide6 import QtCore, QtGui, QtWidgets
from math import sqrt

import uiTools

from PySide6.QtWidgets import QMessageBox

# piccole classi di esempio per separare la logica dall'UI
class DistanceUtils:
    @staticmethod
    def _convert_mm(value_mm: float, unit: str) -> float:
        if unit == 'cm':
            return value_mm / 10.0
        if unit == 'm':
            return value_mm / 1000.0
        return value_mm

class AnnotationUtils:
    @staticmethod
    def add_annotation_at_node(node, text: str, offset_mm: float = 200.0):
        pos = node.getWorldTranslation()
        pos_with_offset = QtGui.QVector3D(pos.x(), pos.y(), pos.z() + offset_mm)
        ann = vrAnnotationService.createAnnotation(f'annotation_for_{node.getName()}')
        ann.setSceneNode(node)
        ann.setPosition(pos_with_offset)
        ann.setText(text)
        return ann
    
    @staticmethod
    def remove_annotations_for_nodes(nodes):
        anns = vrAnnotationService.getAnnotations()
        to_delete = [a for a in anns if a.getSceneNode() in nodes]
        if to_delete:
            vrAnnotationService.deleteAnnotations(to_delete)
        return len(to_delete)


form, base = uiTools.loadUiType('measurement_tool.ui')

class MeasurementTool(form, base):
    def __init__(self, parent=None):
        super(MeasurementTool, self).__init__(parent)
        parent.layout().addWidget(self)
        self.parent = parent
        self.setupUi(self)
        self.setupUserInterface()
    
    def setupUserInterface(self):
        '''
        qua dentro ci metto tutti i collegamenti con i vari bottoni
        (cosa succede quando vengono cliccati ecc)
        ed eventuali icone da caricare
        '''
        self.button_stampa_nomi.clicked.connect(self.onButtonStampaNomi)
        self.button_calcola_distanza.clicked.connect(self.onButtonCalcolaDistanza)
        self.btn_add_annotation.clicked.connect(self.onAddAnnotation)
        self.btn_delete_annotations.clicked.connect(self.onRemoveAnnotations)
        self.btn_delete_all_annotations.clicked.connect(self.onDeleteAllAnnotations)
        # per aggiornare il display quando cambia l'unità dal combobox:
        self.unit_comboBox.currentTextChanged.connect(self.onUnitChanged)

    def onButtonStampaNomi(self):
        '''
        Funzione chiamata quando si clicca il pulsante
        Legge la selezione e stampa il nome dell'elemento nel terminale
        '''
        selectedNodes = vrNodeService.getSelectedNodes()

        if len(selectedNodes) == 0:
            print('Nessun elemento selezionato')
        else:
            for node in selectedNodes:
                nodeName = node.getName()
                print(f"Selezionato -> {nodeName}")

    def onButtonCalcolaDistanza(self):
        '''
        calcola la distanza tra due oggetti selezionati
        '''
        selectedNodes = vrNodeService.getSelectedNodes()
        
        if len(selectedNodes) != 2:
            print('Seleziona correttamente 2 soli oggetti')
            return

        node1 = selectedNodes[0]
        node2 = selectedNodes[1]

        '''
        dalla documentazione:
        vrdTransformNode.getWorldTranslation()
        Returns:	The translation vector in world space
        Return type:	QVector3D
        '''
        pos_node1 = node1.getWorldTranslation() 
        pos_node2 = node2.getWorldTranslation()

        self.distance_mm = pos_node1.distanceToPoint(pos_node2)

        # Stampa il risultato
        print(f"=== CALCOLO DISTANZA ===")
        print(f"Oggetto 1: {node1.getName()}")
        print(f"Posizione 1: ({pos_node1.x():.2f}, {pos_node1.y():.2f}, {pos_node1.z():.2f})")
        print(f"Oggetto 2: {node2.getName()}")
        print(f"Posizione 2: ({pos_node2.x():.2f}, {pos_node2.y():.2f}, {pos_node2.z():.2f})")
        print(f"Distanza: {self.distance_mm:.2f} mm")
        print(f"========================")

        self._refresh_display(self.distance_mm)
    
    def _refresh_display(self, d):
        '''
        Aggiorna il QLCDNumber con l'unità scelta.
        '''
        unit = self.unit_comboBox.currentText() if hasattr(self, 'unit_comboBox') else 'mm'
        value = DistanceUtils._convert_mm(d, unit)
        self.lcdNumber.display(round(value, 2))
    
    def onUnitChanged(self):
        self._refresh_display(self.distance_mm)

    def onAddAnnotation(self):
        selected = vrNodeService.getSelectedNodes()
        if not selected:
            print('Select at least one item!')
            return
        text = self.annotation_text_edit.text().strip() if hasattr(self, 'annotation_text_edit') else ''
        created = 0
        for node in selected:
            t = text or node.getName()
            AnnotationUtils.add_annotation_at_node(node, t, offset_mm=200.0)
            created += 1
        print(f'Created annotations: {created}')

    def onRemoveAnnotations(self):
        selected = vrNodeService.getSelectedNodes()
        if not selected:
            print('Seleziona almeno un oggetto')
            return
        removed = AnnotationUtils.remove_annotations_for_nodes(selected)
        print(f'Annotazioni rimosse: {removed}')

    def onDeleteAllAnnotations(self):
        '''
        Elimina tutte le annotazioni presenti nella scena
        '''
        all_annotations = vrAnnotationService.getAnnotations()
        
        if len(all_annotations) == 0:
            QMessageBox.information(self, "Info", "There are no annotations to delete.")
            return
        
        # Chiedi conferma all'utente
        reply = QMessageBox.question(
            self,
            "Confirm",
            f"Are you sure you want to delete all {len(all_annotations)} annotations?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            vrAnnotationService.deleteAnnotations(all_annotations)
            QMessageBox.information(self, "Success", f"Deleted {len(all_annotations)} annotations.")
            print(f"Deleted all {len(all_annotations)} annotations")

    

measurement_tool = MeasurementTool(VREDPluginWidget)
