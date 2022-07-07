import threading
import odoo

from odoo import models, api, fields


class ATR(models.Model):
    _inherit = 'atr'

    def _run_process_load_address(self, cursor, sql, ids):
        """Aplicar el multiproceso"""
        with odoo.registry(self.env.cr.dbname).cursor() as new_cr:
            new_env = api.Environment(new_cr, self.env.uid, self.env.context)
            # Consulta
            records = new_env['res.partner'].browse(ids)
            cursor = cursor.cursor()
            for rec in records:
                cursor.execute(sql.replace('{vat}', f"'{rec.vat}'"))
                address_data = cursor.fetchall()
                print(f'\n\n{address_data}\n\n')
                break
                # Filtrar direcciones
                if address_data:
                    filter_data = list(filter(lambda x: x[5] is not None or x[6] is not None, address_data))
                    if filter_data:
                        address = filter_data[0]
                    else:
                        address = address_data[0]
                    country_id = new_env.ref('base.ve', raise_if_not_found=False)
                    state_id = new_env.ref('territorial_pd.state_ve_14', raise_if_not_found=False)
                    municipality_id = new_env.ref('territorial_pd.municipio_1409', raise_if_not_found=False)
                    parish_id = address[2].strip()
                    city = ''

                    # Obtener la parroquia
                    if parish_id == 'Caucaguita':
                        parish_id = new_env.ref('territorial_pd.parroquia_140903', raise_if_not_found=False).id
                    elif parish_id == 'Filas de Mariche':
                        parish_id = new_env.ref('territorial_pd.parroquia_140904', raise_if_not_found=False).id
                    elif parish_id == 'La Dolorita':
                        parish_id = new_env.ref('territorial_pd.parroquia_140905', raise_if_not_found=False).id
                    elif parish_id == 'Petare':
                        parish_id = new_env.ref('territorial_pd.parroquia_140901', raise_if_not_found=False).id
                    elif parish_id == 'Leoncio Martinez':
                        parish_id = new_env.ref('territorial_pd.parroquia_140902', raise_if_not_found=False).id
                    else:
                        city = parish_id
                        parish_id = False

                    street = address[3].strip()
                    street2 = address[4].strip()
                    partner_latitude = address[5]
                    partner_longitude = address[6]
                    data = {
                        'country_id': country_id.id,
                        'state_id': state_id.id,
                        'municipality_id': municipality_id.id,
                        'parish_id': parish_id,
                        'street': street,
                        'street2': street2,
                        'city': city,
                        'partner_latitude': partner_latitude,
                        'partner_longitude': partner_longitude,
                    }
                    rec.write(data)

    def create_update_address(self):
        """Actualizar dirección de contactos"""
        cursor_ids = self.env['atr.connect'].search([('type', '=', 'atr')])
        for cursor in cursor_ids:
            company_id = cursor.company_id
            cursor = cursor.credentials_atr()
            # Obtener log
            log_id = self.get_last_log(self.env.cr, company_id)
            if not log_id:
                continue

            # Consulta SQL
            records = self.env['res.partner'].search([
                ('vat', '!=', False),
                ('company_id', '=', company_id.id),
            ], offset=log_id.flag, limit=self.lote).ids

            length = len(records)  # Longitud de las listas
            list_1, list_2, list_3, list_4, list_5, list_6 = [records[i * length // 6: (i + 1) * length // 6] for i in range(6)]

            # Separando los procesos
            process_1 = threading.Thread(target=self._run_process_load_address, args=(cursor, self.sql, list_1))
            process_2 = threading.Thread(target=self._run_process_load_address, args=(cursor, self.sql, list_2))
            process_3 = threading.Thread(target=self._run_process_load_address, args=(cursor, self.sql, list_3))
            process_4 = threading.Thread(target=self._run_process_load_address, args=(cursor, self.sql, list_4))
            process_5 = threading.Thread(target=self._run_process_load_address, args=(cursor, self.sql, list_5))
            process_6 = threading.Thread(target=self._run_process_load_address, args=(cursor, self.sql, list_6))

            # Iniciando los procesos
            process_1.start()
            process_2.start()
            process_3.start()
            process_4.start()
            process_5.start()
            process_6.start()

            import_total = len(records)
            ignore = import_total - import_total

            # Establecer el log
            log_id.date_end = fields.Datetime.now()
            log_id.ignore += ignore
            log_id.flag += import_total
            # print(f'\n\n{len(list_1)}\n\n{len(list_2)}\n\n{list_6}\n\n')
