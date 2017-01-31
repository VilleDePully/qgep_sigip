#!/usr/bin/env python
# -*- coding: utf-8 -*-

import psycopg2, psycopg2.extras
from qgis.PyQt.QtXml import QDomDocument
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import QgsProject, QgsCoordinateReferenceSystem, QgsMapLayerRegistry, QgsMapLayer
from qgis.utils import iface

import qgis2compat.apicompat

original_project = '/home/drouzaud/Documents/QGEP/sige/QGEP/project/qgep_en.qgs'
new_project = '/home/drouzaud/Documents/QGEP/sige/qgis-project/qgep_sige_auto.qgs'


def translate():
  # open original QGEP project
  QgsProject.instance().read(original_project)
  QCoreApplication.processEvents()
  QgsProject.instance().setFileName(original_project)


  # make copy of the project

  QgsProject.instance().write(new_project)
  QCoreApplication.processEvents()
  QgsProject.instance().setFileName(new_project)

  pg_service = "pg_qgep"


  layers = {
    'vw_qgep_wastewater_structure':
    {'name': 'chambre',
     'tabs': {'General': u'Général',
        'Cover': 'Couvercle',
        'Wastewater Structure': 'Ouvrage',
        'Manhole': 'Chambre',
        'Special Structure': u'Ouvrage spécial',
        'Discharge Point': 'Exutoir',
        'Infiltration Installation': 'Installation d''infiltration',
        'Wastewater Node': 'Noeud',
        'Covers': 'Couvercles',
        'Structure Parts': u'Elément d''ouvrage',
        'Maintenance': 'Maintenance',
        'Wastewater Nodes': 'Noeuds',
        'Files': 'Fichiers'},
     'additional_translations': {'manhole_function': 'fonction'}
    },
    'vw_qgep_reach':
    {'name': u'tronçon',
     'tabs': {'General': 'Général',
        'Reach': 'Tronçon',
        'Wastewater Networkelement': u'Element du réseau',
        'Channel': 'Canalisation',
        'Wastewater Structure': 'Ouvrage',
        'Reach Points': 'Point de tronçon',
        'Maintenance': 'Maintenance'},
     'additional_translations': {}
    }
  }

  # connect to db
  conn = psycopg2.connect("service={0}".format(pg_service))
  cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

  # set SRID to 2056
  iface.mapCanvas().setDestinationCrs(QgsCoordinateReferenceSystem(2056)) # TODO QGIS3 use QgsProject.instance().setCrs instead
  for layer in QgsMapLayerRegistry.instance().mapLayers().values():

    if layer.type() != QgsMapLayer.VectorLayer:
      QgsMapLayerRegistry.instance().removeMapLayer(layer)

    elif layer.hasGeometryType():
      layer.setCrs(QgsCoordinateReferenceSystem(2056))

      source = layer.source().replace('21781','2056')

      document = QDomDocument("style")
      map_layers_element = document.createElement("maplayers")
      map_layer_element = document.createElement("maplayer")
      layer.writeLayerXml(map_layer_element, document)

      # modify DOM element with new layer reference
      map_layer_element.firstChildElement("datasource").firstChild().setNodeValue(source)
      map_layers_element.appendChild(map_layer_element)
      document.appendChild(map_layers_element)

      # reload layer definition
      layer.readLayerXml(map_layer_element)
      layer.reload()

  # translation
  for layer in QgsMapLayerRegistry.instance().mapLayers().values():
    if layer.id() in layers.keys():
      layer.setName(layers[layer.id()]['name'])
      tabs = layer.editFormConfig().tabs()
      # tabs
      for tab in layer.editFormConfig().tabs():
        if tab.name() in layers[layer.id()]['tabs']:
          tab.setName(layers[layer.id()]['tabs'][tab.name()])
        else:
          print("Tab {0} not translated".format(tab.name()))
      # fields
      for idx,field in enumerate(layer.fields()):
        #print(layer.name(),idx,field.name())
        # translation
        trans = get_field_translation(cur, field.name())
        if field.name() in layers[layer.id()]['additional_translations']:
          layer.addAttributeAlias(idx, layers[layer.id()]['additional_translations'][field.name()])
        elif trans is not None:
          layer.addAttributeAlias(idx, trans)
        else:
          print("Field {0} is not translated".format(field.name()))

        # update value relation value
        if layer.editFormConfig().widgetType(idx) == 'ValueRelation':
          cfg = layer.editFormConfig().widgetConfig(idx)
          if cfg["Value"] == "value_en":
            cfg["Value"] = "value_fr"
            layer.editFormConfig().setWidgetConfig(idx, cfg)

        # value maps
        if layer.editFormConfig().widgetType(idx) == 'ValueMap':
          cfg = layer.editFormConfig().widgetConfig(idx)
          for key in cfg.keys():
            trans = get_table_translation(cur, cfg[key])
            if trans:
              cfg[trans] = cfg[key]
              del cfg[key]
          layer.editFormConfig().setWidgetConfig(idx, cfg)

  # remove group
  tree_root = QgsProject.instance().layerTreeRoot()
  grp = tree_root.findGroup('Cadastral Data')
  if grp:
    tree_root.removeChildNode(grp)

  # background layers
  newGroup = QgsProject.instance().createEmbeddedGroup( "Cadastre", "/home/drouzaud/Documents/QGEP/sige/cadastre/cadastre_pg.qgs", [] )
  if newGroup:
    QgsProject.instance().layerTreeRoot().addChildNode( newGroup )


  # save project
  QgsProject.instance().write(new_project)




def get_field_translation(cursor, field):
  cursor.execute("SELECT field_name_fr FROM qgep.is_dictionary_od_field WHERE field_name = '{0}' LIMIT 1".format(field))
  trans = cursor.fetchone()
  if trans is None:
      return None
  else:
      return trans[0].lower()

def get_table_translation(cursor, table):
  cursor.execute("SELECT name_fr FROM qgep.is_dictionary_od_table WHERE tablename LIKE '%{0}' LIMIT 1".format(table))
  trans = cursor.fetchone()
  if trans is None:
      return None
  else:
      return trans[0].lower()
