from odoo import fields, models
# from mpl_toolkits.mplot3d import axes3d
import numpy as np
import io
import base64
import matplotlib
import matplotlib.pyplot as plt
import matplotlib as mpl
from cycler import cycler
import matplotlib.ticker as mtick
import matplotlib.patheffects as path_effects


class WizardReports(models.TransientModel):
    _name = 'wizard.reports'
    _description = 'Wizard de Reportes Estadisticos'

    date_start = fields.Date('Fecha Inicio', required=True)
    date_end = fields.Date('Fecha Fin', required=True)
    tax_ids = fields.Many2many('account.tax.return', string="Declaraciones")
    # payment_ids = fields.Many2many('account.tax.return', string="Planillas de pagos")

    def create_report_municipal_comparison_graphic(self):
        """Crear reporte del comparativo municipal"""
        tax_ids = self.env['account.tax.return'].search(
            [('date', '>=', self.date_start), ('date', '<=', self.date_end),
             ('type_tax', '=', 'tax')])
        if tax_ids:
            self.tax_ids = [(6, 0, tax_ids.ids)]
            action = self.env.ref(
                'declaration_tax_return.report_municipal_comparison_action').sudo().report_action(self)
            return action

    def retun_graph_base64(self, users):
        mpl.rc('lines', linewidth=2.)
        # fondo de la grafica
        mpl.rc('axes', facecolor='#0b1870', edgecolor='#0b1870')
        # color de las lineas
        mpl.rc('xtick', color='w')
        mpl.rc('ytick', color='#0b1870')
        mpl.rc('text', color='w')
        # tamano de la letra
        mpl.rc('font', size=8)
        # color de la cuadricula
        mpl.rc('grid', color='k')
        mpl.rc('grid', linewidth=1.0)
        # fondo de la grafica total
        mpl.rc('figure', facecolor='#0b1870', edgecolor='k')
        # https://matplotlib.org/1.4.0/users/customizing.html
        width = 0.20
        fontsize = '8'
        # Define ancho de las bars
        ancho_barras = 0.2

        l = ['#2f5597', '#ffc000', '#5b9bd5', '#1f4e79', '#92d050', '#00b050', '#ff6600', '#660066']
        
        teams = ['Estados', 'España', 'Mexico', 'Rusia', 'Japon', 'Venezuela',
                 'Italia', 'Australia']
        wincount = [21, 34, 20, 25, 32, 37, 15, 30]

        plt.xlabel("")
        plt.ylabel(" ")
        plt.title("Fecha de Reporte")

        for i in range(0, len(teams) + 1):
            l.append(tuple(np.random.choice(range(0, 2), size=3)))

        plt.bar(teams, wincount, color=l, width=ancho_barras)
        width = 0.2

        # desde aqui
        #   tamaño de la imagen
        fig, ax = plt.subplots(figsize=(9, 4))
        # La leyenda de la derecha
        ax2 = ax.twinx()
        # Grafico de Barras
        p1 = ax2.bar(teams, wincount, color=l, edgecolor='gray', label='Barra')

        for p in p1:
            height = p.get_height()
            ax2.text(x=p.get_x() + p.get_width() / 2, y=height + -1.70,
                     s="{}%".format(height),
                     ha='center', weight='bold')

        fmt = '%.0f%%'  # Formato para imprimir el simbolo de Porcentaje %
        yticks = mtick.FormatStrFormatter(fmt)
        ax2.yaxis.set_major_formatter(yticks)

        img = io.BytesIO()
        plt.savefig(img, dpi=100, format='png', transparent=False)
        plt.close()
        return base64.b64encode(img.getvalue())



    def retun_graph_base64_2(self, users):
        # Definiendo el tamaño de la fuente a utilizar en el eje Y y en la leyenda
        mpl.rc('lines', linewidth=2.)
        # fondo de la grafica
        mpl.rc('axes', facecolor='#0b1870', edgecolor='#b3b4b5')
        # color de las lineas
        mpl.rc('axes', prop_cycle=(cycler('color', ['b', 'b', 'b'])))

        # modificar el color del texto
        mpl.rc('xtick', color='k')
        mpl.rc('ytick', color='k')
        mpl.rc('text', color='k')

        # tamano de la letra
        mpl.rc('font', size=8)
        # color de la cuadricula
        mpl.rc('grid', color='k')
        mpl.rc('grid', linewidth=1.0)
        # fondo de la grafica total
        mpl.rc('figure', facecolor='#0b1870', edgecolor='k')
        width = 0.35
        fontsize = '8'
        # Define ancho de las bars
        ancho_barras = 0.25

        small = '7'
        plt.rc('xtick', labelsize=small)
        plt.rc('legend', fontsize=small)
        # Definiendo las tuplas

        municipality = ['EL TIGRE', 'EL HATILLO', 'MANEIRO', 'LECHERIA',
                        'SAN DIEGO', 'BARUTA', 'CHACAO', 'SUCRE']
        raised = [20, 35, 30, 35, 27, 40, 5, 1]
        pending = [25, 32, 34, 20, 25, 10, 14, 28]
        
        bold = {'weight':'bold'}

        # Especificando la barra que debe ir en el eje X
        bottom_raised = raised

        # Definiendo los valores que deben contener las barras bajo el valor de las tuplas correspondientes
        fig, ax = plt.subplots(figsize=(11, 3))
        p1 = ax.bar(municipality, raised, color='#3b569c', label='RECAUDADO')
        p2 = ax.bar(municipality, pending, bottom=bottom_raised,
                    color='#d9e7fa', label='PENDIENTE')

        # Asignando valores dentro de las barras
        ax.bar_label(p1, color='white', label_type='center', weight='bold')
        ax.bar_label(p2, color='#1371f0', label_type='center', weight='bold')

        # Funciones de formateo para mostrar en el eje Y valores en %
        fmt = '%.0f%%'
        xticks = mtick.FormatStrFormatter(fmt)
        ax.yaxis.set_major_formatter(xticks)

        # Definiendo parametros en la leyenda para ajustar la posicion de la misma
        legend = ax.legend(handles=[p2], frameon=False,
                           bbox_to_anchor=(0.7, -0.06), prop=bold)
        ax.add_artist(legend)
        ax.legend(handles=[p1], frameon=False, bbox_to_anchor=(0.4, -0.06), prop=bold)
        ax.set_axisbelow(True)
        ax.yaxis.grid(color='white')

        # Definiendo en el eje y la secuencia en porcentajes
        ax.set_yticks([0, 25, 50, 75, 100])

        # Asignando el color del background a la grafica y el color dentro de la misma
        fig.patch.set_facecolor('#e7e6e6')
        ax.set_facecolor('#767272')

        img = io.BytesIO()
        plt.savefig(img, dpi=100, format='png', transparent=False)
        plt.close()
        return base64.b64encode(img.getvalue())



    def retun_graph_base64_3(self, users):
        mpl.rc('lines', linewidth=2.0)
        mpl.rc('axes', facecolor='#132864', edgecolor='#132864')
        mpl.rc('axes', prop_cycle=(cycler('color', ['b', 'b', 'b'])))
        mpl.rc('xtick', color='w')
        mpl.rc('ytick', color='w')
        mpl.rc('text', color='w')
        mpl.rc('font', size=12)
        mpl.rc('grid', color='#8593b1')
        mpl.rc('grid', linewidth=0.7)
        mpl.rc('figure', facecolor='#132864', edgecolor='w')
        # https://matplotlib.org/1.4.0/users/customizing.html

        meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo']
        bar = [2, 3, 3.3, 3.5, 2.7]
        line = [250, 262, 277, 275, 272]

        # Define ancho de las bars
        ancho_barras = 0.25

        fig, ax = plt.subplots(figsize=(10, 3))

        # tamaño de la imagen

        # La leyenda de la derecha
        ax2 = ax.twinx()
        # Grafico de Barras
        p1 = ax2.bar(meses, bar, color='white', edgecolor='#132864',
                     label='Barra', width=ancho_barras)
        # Funcion para imprimir %
        for p in p1:
            height = p.get_height()
            ax2.text(x=p.get_x() + p.get_width() / 2, y=height + .10,
                     s="{}%".format(height),
                     ha='center')
        # Grafico de Linea
        p2 = ax.plot(meses, line, color='#5089bc', label='Linea',
                     path_effects=[path_effects.SimpleLineShadow(),
                                   path_effects.Normal()])  # Efecto de sombra

        # Funcion para imprimir el numero en la linea
        for i, txt in enumerate(line):
            ax.annotate(txt, (meses[i], line[i]), color='white', weight="bold")
        # Leyenda de linea Predefinida
        ax.set_yticks([200, 225, 250, 275, 300])
        # Leyenda de barra Predefinida
        ax2.set_yticks([0, 3, 6, 9, 12])
        plt.grid(axis='y')
        mpl.rc('figure', facecolor='#132864', edgecolor='#132864')

        fmt = '%.0f%%'  # Formato para imprimir el simbolo de Porcentaje %
        yticks = mtick.FormatStrFormatter(fmt)  # -------
        ax2.yaxis.set_major_formatter(yticks)  # ---------

        # ax2.bar_label(p1, label_type='edge')

        # bbox_to_anchor, se le da en que coordenadas saldra la leyenda
        ax.legend(bbox_to_anchor=(0.6, 1.2), frameon=False)
        ax2.legend(bbox_to_anchor=(0.4, 1.2), frameon=False)
        # Cambiar los colores lineas contenedor
        ax2.spines["bottom"].set_color("white")
        ax2.spines["top"].set_color("#8593b1")
        ax2.set_axisbelow(True)


        img = io.BytesIO()
        plt.savefig(img, dpi=100, format='png', transparent=True)
        plt.close()
        return base64.b64encode(img.getvalue())

    def retun_graph_base64_4(self, users):
        mpl.rc('lines', linewidth=2.0)
        mpl.rc('axes', facecolor='#132864', edgecolor='#132864')
        mpl.rc('axes', prop_cycle=(cycler('color', ['b', 'b', 'b'])))
        mpl.rc('xtick', color='w')
        mpl.rc('ytick', color='w')
        mpl.rc('text', color='w')
        mpl.rc('font', size=12)
        mpl.rc('grid', color='w')
        mpl.rc('grid', linewidth=0.7)
        mpl.rc('figure', facecolor='#132864', edgecolor='w')

        mpl.rc('xtick', color='k')
        mpl.rc('ytick', color='k')
        mpl.rc('text', color='k')

        labels = ['EJ1', 'EJ2', 'EJ3', 'EJ4', 'EJ5']
        date_means = [20, 34, 30, 35, 27]
        date2_means = [25, 32, 34, 20, 25]

        x = np.arange(len(labels))  # the label locations
        width = 0.35  # the width of the bars

        fig, ax = plt.subplots(figsize=(10, 4))

        bar1 = ax.bar(x - width / 2, date_means, width, color='#d9dadb',
                      label='Fecha 1')
        bar2 = ax.bar(x + width / 2, date2_means, width, color='#265182',
                      label='Fecha 2')

        # Leyenda que figura en la parte superior izquierda de la tabla
        ax.set_ylabel('MILES')
        ax.yaxis.set_label_coords(-0.1, 1.02)
        # ax.set_xticks(x, labels)

        # Leyenda de cada barra
        first_legend = ax.legend(handles=[bar1], loc='upper center',
                                 fontsize='8', frameon=False,
                                 bbox_to_anchor=(0.1, 1.1))
        ax.add_artist(first_legend)
        ax.legend(handles=[bar2], loc='upper left', fontsize='8',
                  frameon=False, bbox_to_anchor=(0.3, 1.1))

        # Asignando valores dentro de las barras
        ax.bar_label(bar1, color='white', weight='bold')
        ax.bar_label(bar2, color='white', weight='bold')
        
        # Color de fondo de la grafica
        ax.set_facecolor('#555555a1')
        plt.grid(axis='y', color='white', linewidth='0.8')

        ax.spines["bottom"].set_color("white")
        ax.spines["top"].set_color("#888")
        
        # permite colocar las barras de color solido
        ax.set_axisbelow(True)
        img = io.BytesIO()
        plt.savefig(img, dpi=100, format='png', transparent=True)
        plt.close()
        return base64.b64encode(img.getvalue())