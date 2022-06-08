import threading
import time
import pandas as pd

from odoo import models, fields


def parser_number(number):
    """Parsear número telefónico"""
    if number and number[0] == '0':
        number = '+58' + number[1:]
    return number


def parser_string(x):
    """Parsear caracteres"""
    if x:
        x = x.strip().replace(',', '').replace(' ', '').replace('"', '')
        return x
    return ''


def parser_name(x):
    """Parsear caracteres del nombre"""
    if x:
        x = x.strip().replace(',', '').replace('"', '')
        return x
    return ''


def multiprocess_partner_data(x):
    x['vat'] = x['vat'].transform(parser_string)
    x['name'] = x['name'].transform(parser_name)
    x['type_person'] = x['type_person'].transform(parser_string)
    x['active'] = x['active'].transform(parser_string)
    x['email'] = x['email'].transform(parser_string)
    x['email_second'] = x['email_second'].transform(parser_string)
    x['mobile'] = x['mobile'].transform(parser_string)
    x['phone'] = x['phone'].transform(parser_string)

    # Parsear números telefónicos
    x['mobile'] = x['mobile'].transform(parser_number)
    x['phone'] = x['phone'].transform(parser_number)
    return x


class ATR(models.Model):
    _inherit = 'atr'

    def create_partner(self):
        """Crear Partner"""
        cursor_ids = self.env['atr.connect'].search([('type', '=', 'atr')])
        for cursor in cursor_ids:
            time. sleep(60)
            company_id = cursor.company_id
            cursor = cursor.credentials_atr()
            # Obtener log
            log_id = self.get_last_log(cursor.cursor(), company_id)
            if not log_id:
                continue
            # Consulta SQL
            sql_query = pd.read_sql_query(self.sql.replace('{offset}', str(log_id.flag)).replace('{limit}', str(self.lote)), cursor)
            df_partner = pd.DataFrame(sql_query)  # Convertir la consulta en un dataframe
            header = ['vat', 'name', 'type_person',
                      'active', 'email', 'email_second', 'mobile',
                      'phone', 'id']
            df_partner.columns = header  # Asignando el nuevo header

            # Creando nuevas columnas
            df_partner['company_id.id'] = company_id.id
            df_partner['is_company'] = 'True'

            df_partner = df_partner.groupby(["type_person"]).apply(multiprocess_partner_data)

            # Cambiar valores de las columnas según una condición
            df_partner.loc[df_partner.active == 'ACTIVO', 'active'] = 'True'
            df_partner.loc[df_partner.active == 'INACTIVO', 'active'] = 'False'
            df_partner.loc[df_partner.name == '', 'name'] = 'S/N'
            df_partner.loc[df_partner.type_person != 'JURIDICO', 'is_company'] = 'False'

            # Borrar filas que no tienen rif
            total = len(df_partner)
            df_partner.drop(df_partner.loc[df_partner['vat'] == ''].index, inplace=True)

            df_partner['id'] = df_partner['id'].map('partner_{}'.format).values
            company_name = company_id.name.replace(' ', '_')
            df_partner['id'] = df_partner['id'].str.replace('partner_', f'partner_{company_name.lower()}_')

            # Multiproceso
            list_df = df_partner.to_numpy().tolist()  # Convertir dataframe en lista
            length = len(list_df)  # Longitud de las listas
            list_1, list_2, list_3, list_4, list_5, list_6 = [list_df[i * length // 6: (i + 1) * length // 6] for i in range(6)]

            # Separando los procesos
            process_1 = threading.Thread(target=self._run_process_load, args=(';'.join(list(df_partner.columns)), 'res.partner', list_1))
            process_2 = threading.Thread(target=self._run_process_load, args=(';'.join(list(df_partner.columns)), 'res.partner', list_2))
            process_3 = threading.Thread(target=self._run_process_load, args=(';'.join(list(df_partner.columns)), 'res.partner', list_3))
            process_4 = threading.Thread(target=self._run_process_load, args=(';'.join(list(df_partner.columns)), 'res.partner', list_4))
            process_5 = threading.Thread(target=self._run_process_load, args=(';'.join(list(df_partner.columns)), 'res.partner', list_5))
            process_6 = threading.Thread(target=self._run_process_load, args=(';'.join(list(df_partner.columns)), 'res.partner', list_6))

            # Iniciando los procesos
            process_1.start()
            process_2.start()
            process_3.start()
            process_4.start()
            process_5.start()
            process_6.start()

            import_total = len(df_partner)
            ignore = total - import_total
            # Establecer el log
            log_id.date_end = fields.Datetime.now()
            log_id.ignore += ignore
            log_id.flag += total
