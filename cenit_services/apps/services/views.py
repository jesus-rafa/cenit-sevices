import os
import jinja2
import pdfkit
import qrcode
import shutil
import pytz
from datetime import datetime
from dateutil import parser
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from supabase import create_client, Client
from django.conf import settings
from rest_framework.response import Response
from rest_framework import generics, status
from matplotlib import font_manager
load_dotenv()


class Generate_Certificate(generics.GenericAPIView):
    def get_serializer_class(self):
        return None
    
    def get(self, request, *args, **kwargs):
        url: str = os.getenv('SUPABASE_URL')
        key: str = os.getenv('SUPABASE_KEY')

        if getattr(self, 'swagger_fake_view', False):
            return Response()
        
        DEBUG = os.getenv('DEBUG')
        if  DEBUG == 'True':
            # Path Local
            path_base = 'file:///Repos/cenit/services/cenit-services/cenit_services/'
            # Windows
            config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
            
        else:
            #Path Producción
            path_base = 'file:///app/'
            # Linux
            config = pdfkit.configuration(wkhtmltopdf='/usr/bin/wkhtmltopdf')

        def convert_utc_to_mexico_tz(time_str):
            # Convertir la fecha a formato UTC ISO 8601
            dt = parser.isoparse(time_str)   
            utc_time_str = dt.strftime('%Y-%m-%dT%H:%M:%SZ')
            utc_time = datetime.strptime(utc_time_str, '%Y-%m-%dT%H:%M:%SZ')
            utc_time = utc_time.replace(tzinfo=pytz.UTC)
            mexico_tz = pytz.timezone('America/Mexico_City')
            local_time = utc_time.astimezone(mexico_tz)
            return local_time
        
        def convert_utc_to_mexico_tz_chart(time_str):
            dt = parser.isoparse(time_str)   
            return dt.astimezone(pytz.timezone('America/Mexico_City'))
        
        def convert_utc_to_mexico_tz_str(time_str):
            if pd.isna(time_str) or time_str == '':
                return None 
            return convert_utc_to_mexico_tz(time_str).strftime('%d/%m/%Y %I:%M:%S %p')

        def generate_report(file_name, data):
            env = jinja2.Environment(loader=jinja2.FileSystemLoader('media/data'))
            template = env.get_template('template.html')
            html = template.render(data)
            options = {
                'enable-local-file-access': None,
                'page-size': 'Letter',
                'margin-top': '0.5in',
                'margin-right': '0.2in',
                'margin-left': '0.2in',
                'margin-bottom': '0.2in',
                'encoding': 'UTF-8'
            }
            
            path_output = 'media/data/pdf/' + file_name
            pdfkit.from_string(html, path_output, options=options, configuration=config)
        
        def clear_folder(folder_path):
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f'Error al borrar {file_path}. Razón: {e}')
                    
        try:
            supabase: Client = create_client(url, key)
        except Exception as e:
            status_resp = 'error'
            code = status.HTTP_404_NOT_FOUND
            message = str(e)
            data = False

        # Obtener Parametros
        subscription_id = self.kwargs['subscription_id']
        proof_id = self.kwargs['proof_id']
        path_output = os.path.join(settings.MEDIA_ROOT + '/data/pdf/', proof_id + '.pdf')

        try:
            # Especifica la ruta a la fuente que descargaste
            font_path = os.path.join(settings.MEDIA_ROOT + '/data/fonts/SpaceGrotesk-Regular.ttf')
            # Cargar la fuente
            font_prop = font_manager.FontProperties(fname=font_path)

            ### DATOS MAESTROS -START
            response_master = supabase.table(
                'vw_proofs'
            ).select(
                'id_seguimiento, fecha_creacion, fecha_fin, numero_serie, enfriador, usuario, bodega, duracion, resultado, descripcion, observaciones, tipo_enfriador, suscripcion_id'
            ).eq(
                'id_seguimiento', proof_id
            ).execute()
            
            if response_master.data:
                response_master.data[0]['fecha_creacion'] = convert_utc_to_mexico_tz_str(response_master.data[0]['fecha_creacion'])
                response_master.data[0]['fecha_fin'] = convert_utc_to_mexico_tz_str(response_master.data[0]['fecha_fin'])
                # Determina el valor de iconStatusProof basado en el valor de resultado
                resultado = response_master.data[0].get('resultado')
                if (resultado):
                    iconStatusProof = "media/data/check_circle.png"
                else:
                    iconStatusProof = "media/data/close_circle.png"
                
                # Generar QR
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=20,
                    border=4,  # Margen alrededor del código QR
                )
                qr_data = f"{response_master.data[0]['numero_serie']}-{proof_id}"
                qr.add_data(qr_data)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")

                # Convertir la imagen a un objeto de Pillow
                img = img.convert("RGB")

                # Recortar el margen blanco
                def crop_image(image):
                    # Convertir la imagen a modo "L" (escala de grises)
                    image = image.convert("L")
                    # Obtener los datos de los píxeles
                    pixels = image.getdata()
                    # Encontrar el valor del blanco
                    white = 255
                    # Convertir a una lista para procesar
                    pixels = list(pixels)
                    # Encontrar el índice del primer píxel no blanco
                    min_x = min_y = float('inf')
                    max_x = max_y = -float('inf')
                    width, height = image.size

                    for y in range(height):
                        for x in range(width):
                            if pixels[y * width + x] != white:
                                min_x = min(min_x, x)
                                max_x = max(max_x, x)
                                min_y = min(min_y, y)
                                max_y = max(max_y, y)

                    # Recortar la imagen
                    bbox = (min_x, min_y, max_x + 1, max_y + 1)
                    cropped_image = image.crop(bbox)
                    return cropped_image

                # Recortar la imagen QR para eliminar el margen blanco
                cropped_img = crop_image(img)

                # Guardar la imagen recortada
                img_path_qr = os.path.join(settings.MEDIA_ROOT, 'data/qr', f"{proof_id}.png")
                cropped_img.save(img_path_qr)

                data_master = response_master.data[0]
            else:
                data_master = []
            ### DATOS MAESTROS -END

            ### GRAFICA TEMPERATURA - START
            response = supabase.table(
                'temperatures'
            ).select(
                'devices(serial_number), recorded_at, value'
            ).eq(
                'proof_id', proof_id
            ).execute()  
            
            plt.figure(figsize=(20, 5))
            plt.subplots_adjust(left=0.04, right=0.99, top=0.99)
            # plt.title('Gráfica de temperatura', fontweight='bold', fontsize=20, fontproperties=font_prop)
            if response.data:
                data_temp = response.data
                df_temp = pd.json_normalize(data_temp)

                # Obtener la primera y última fecha antes de la conversión de zona horaria
                first_date = df_temp['recorded_at'].min()
                last_date = df_temp['recorded_at'].max()
                
                # dispositivo temperatura ambiente
                deviceAmbient = supabase.table(
                    'vw_devices'
                ).select(
                    'device_id'
                ).eq(
                    'suscripcion_id', data_master['suscripcion_id']
                ).eq(
                    'dispositivo', 'sensor-ambient'
                ).execute()

                if deviceAmbient.data:
                    device_id = deviceAmbient.data[0]['device_id'] if deviceAmbient.data else None
                    # Consultar registros dentro del rango de fechas
                    response_within_range = supabase.table(
                        'temperatures_ambient'
                    ).select(
                        'devices(serial_number), recorded_at, value'
                    ).eq(
                        'device_id', device_id
                    ).gte(
                        'recorded_at', first_date
                    ).lte(
                        'recorded_at', last_date
                    ).execute()

                    data_temp_ambient = response_within_range.data
                    # print(response_within_range, data_temp_ambient)
                
                df_temp['recorded_at'] = df_temp['recorded_at'].apply(convert_utc_to_mexico_tz_chart)
                
                if(deviceAmbient.data and data_temp_ambient):
                    df_tempAmbient = pd.json_normalize(data_temp_ambient)
                    df_tempAmbient['devices.serial_number'] = "Ambiente"    
                    df_tempAmbient['recorded_at'] = df_tempAmbient['recorded_at'].apply(convert_utc_to_mexico_tz_chart)
                    
                    # Agregar un registro al inicio del sernsor de ambiente
                    first_value = df_tempAmbient['value'].iloc[0] if not df_tempAmbient.empty else None
                    first_date_ = convert_utc_to_mexico_tz_chart(first_date)
                    # Crear una nueva fila con first_date y el primer valor antes de la fecha de rango
                    if first_value and first_date_ is not None:
                        new_row_start = {
                            'devices.serial_number': "Ambiente",
                            'recorded_at': first_date_,
                            'value': first_value
                        }
                        df_tempAmbient = pd.concat([pd.DataFrame([new_row_start]), df_tempAmbient], ignore_index=True)

                    # Obtener el último valor y la última fecha en df_tempAmbient
                    last_value = df_tempAmbient['value'].iloc[-1] if not df_tempAmbient.empty else None
                    last_date_ = convert_utc_to_mexico_tz_chart(last_date)
                    # Crear una nueva fila con last_date y last_value
                    if last_date and last_value is not None:
                        new_row = {
                            'devices.serial_number': "Ambiente",
                            'recorded_at': last_date_,
                            'value': last_value
                        }
                        df_tempAmbient = pd.concat([df_tempAmbient, pd.DataFrame([new_row])], ignore_index=True)

                    # Concatenar df_temp y df_tempAmbient
                    df_temp = pd.concat([df_temp, df_tempAmbient], axis=0)

                # # Obtener los últimos 10 registros de cada sensor y calcular promedio
                # average_temperatures = {}
                # for sensor in df_temp['devices.serial_number'].unique():
                #     sensor_data = df_temp[df_temp['devices.serial_number'] == sensor].tail(10)
                #     average_temperatures[sensor] = sensor_data['value'].mean()
                # #Formatear la salida a 2 decimales   
                # average_temperatures = {key: "{:.2f}".format(value) for key, value in average_temperatures.items()}
                # average_temperatures_list = [(key, value) for key, value in average_temperatures.items()]

                # Obtener la última temperatura de cada sensor
                latest_temperatures = {}
                for sensor in df_temp['devices.serial_number'].unique():
                    sensor_data = df_temp[df_temp['devices.serial_number'] == sensor].tail(1)
                    latest_temperatures[sensor] = sensor_data['value'].values[0]  # Obtener el valor más reciente

                # Formatear la salida a 2 decimales
                latest_temperatures = {key: "{:.2f}".format(value) for key, value in latest_temperatures.items()}

                # Convertir el diccionario en una lista de tuplas (opcional)
                latest_temperatures_list = [(key, value) for key, value in latest_temperatures.items()]

                sensors = df_temp['devices.serial_number'].unique()
                # colors = ["#19124A", "#5E45F9", "#06394F", "#1D901F"]
                colors = ['#19124A', '#5E45F9', '#787680', '#19124A']
                sensor_color_mapping = {serial_number: colors[i] for i, serial_number in enumerate(sensors)}

                # Generar un plot por cada sensor
                for i, serial_number in enumerate(sensors):
                    device_data = df_temp[df_temp['devices.serial_number'] == serial_number]
                    # print(device_data)
                    plt.plot(device_data['recorded_at'], device_data['value'], label=f'Sensor: {serial_number}', color=colors[i])
            else:
                plt.plot([], [], label='No se encontraron datos', color=colors[0])
                # average_temperatures_list = []
                latest_temperatures_list = []
                sensor_color_mapping = []

            # plt.xlabel('Tiempo', fontweight='bold', fontsize=18)
            plt.ylabel('temperatura (°C)', fontweight='bold', fontsize=18, fontproperties=font_prop)
            plt.grid(True, alpha=0.3)
            plt.legend(loc='best',fontsize=16)
            fig_path_temperature = os.path.join(settings.MEDIA_ROOT + '/data/plot/' + f"{proof_id}_temperatura.png")
            plt.savefig(fig_path_temperature, format='png', dpi=100)
            plt.clf()
            plt.close()
            ### GRAFICA TEMPERATURA - END
                        
            ### GRAFICA CONSUMO - START
            responseEnergies = supabase.table('energies').select(
                'devices(serial_number), recorded_at, value'
            ).eq(
                'proof_id', proof_id
            ).execute()
            if responseEnergies.data:
                dfEnergies = pd.json_normalize(responseEnergies.data)
                #dfEnergies['recorded_at'] = pd.to_datetime(dfEnergies['recorded_at'])
                dfEnergies['recorded_at'] = dfEnergies['recorded_at'].apply(convert_utc_to_mexico_tz_chart)

                last_entry = dfEnergies['value'].iloc[-1]
                last_entry ="{:.2f}".format(last_entry)
            else:
                last_entry = "0.0"
            ### GRAFICA CONSUMO - END

            ### GRAFICA VOLTAJE -START
            responseVoltages = supabase.table('voltages').select(
                'devices(serial_number), recorded_at, value'
            ).eq(
                'proof_id', proof_id
            ).execute()

            plt.figure(figsize=(20, 3))
            plt.subplots_adjust(left=0.04, right=0.99, top=0.95)
            # plt.title('Gráfica de voltaje', fontweight='bold', fontsize=20)
            if responseVoltages.data:
                dfVoltages = pd.json_normalize(responseVoltages.data)
                dfVoltages['recorded_at'] = dfVoltages['recorded_at'].apply(convert_utc_to_mexico_tz_chart)
                plug = dfVoltages['devices.serial_number'].iloc[0]
                # Calculos Voltaje 
                # Obtener todos los voltajes
                voltages = dfVoltages['value']
                # Calcular el promedio de voltajes y darle formato a 2 decimales
                average_voltage = "{:.2f}".format(voltages.mean())
                plt.plot(dfVoltages['recorded_at'], dfVoltages['value'], label=f'Plug: {plug}', color=colors[0])
        
            else:
                # Generar gráfica vacía con leyenda "No se encontraron datos"
                plt.plot([], [], label='No se encontraron datos', color=colors[0])
                average_voltage = "0.00"  # Variable en 0

            plt.ylim(100, 140)
            plt.yticks([100, 120, 140])
            plt.grid(True, alpha=0.3)
            plt.legend(loc='best',fontsize=16)
            # plt.xlabel('Tiempo', fontweight='bold', fontsize=18)
            plt.ylabel('voltaje (V)', fontweight='bold', fontsize=18, fontproperties=font_prop)
            fig_path_voltage = os.path.join(settings.MEDIA_ROOT + '/data/plot/' + f"{proof_id}_voltaje.png")
            plt.savefig(fig_path_voltage, format='png')
            plt.clf()
            plt.close()
            ### GRAFICA VOLTAJE - END

            ### GRAFICA CORRIENTE -START
            responseCurrents = supabase.table('currents').select(
                'devices(serial_number), recorded_at, value'
            ).eq(
                'proof_id', proof_id
            ).execute()   

            plt.figure(figsize=(20, 3))
            plt.subplots_adjust(left=0.04, right=0.99, top=0.99)
            # plt.title('Gráfica de corriente', fontweight='bold', fontsize=20)
            if responseCurrents.data:
                dfCurrents = pd.json_normalize(responseCurrents.data)
                dfCurrents['recorded_at'] = dfCurrents['recorded_at'].apply(convert_utc_to_mexico_tz_chart)
                plug = dfCurrents['devices.serial_number'].iloc[0]
                # Calculos Corriente
                # Filtrar los valores de corriente
                current_values = dfCurrents['value']
                # Definir un umbral para separar los valores de corriente de LEDs y enfriador
                threshold = dfCurrents['value'].mean()  # Este valor puede variar según los datos específicos
                # Filtrar los dos momentos
                leds_on = current_values[current_values < threshold]
                cooler_on = current_values[current_values >= threshold]
                # Calcular la moda de cada grupo
                try:
                    leds_mode = leds_on.mode().values[0]
                    cooler_mode = cooler_on.mode().values[0]

                except Exception as e:
                    leds_mode = 0
                    cooler_mode = 0

                plt.plot(dfCurrents['recorded_at'], dfCurrents['value'],label=f'Plug: {plug}', color=colors[0])
                
                try:
                    if abs(leds_mode - dfCurrents['current'].min()) > 1:
                        label_leds = dfCurrents['current'].min() # Valor minimo para texto
                    else:
                        label_leds = leds_mode

                except Exception as e:
                    label_leds = 0
            else:
                plt.plot([], [], label='No se encontraron datos', color=colors[0])
                leds_mode = 0
                cooler_mode = 0
                label_leds = 0

            # plt.xlabel('Tiempo', fontweight='bold', fontsize=18)
            plt.ylabel('amperes (Amp)', fontweight='bold', fontsize=18, fontproperties=font_prop)
            plt.ylim(-0.5, cooler_mode + 1.5)
            cooler_mode = "{:.2f}".format(cooler_mode)
            plt.grid(True, alpha=0.3)
            plt.legend(loc='best',fontsize=16)
            fig_path_current = os.path.join(settings.MEDIA_ROOT + '/data/plot/' + f"{proof_id}_corriente.png")
            plt.savefig(fig_path_current, format='png')
            plt.clf()
            plt.close()            
            ### GRAFICA CORRIENTE - END 

            ### DATOS EMPRESA - START
            response_company = supabase.table(
                'companies'
            ).select(
                'id, created_at, subscription_id, name, logo, e_mail, phone, address'
            ).eq(
                'subscription_id', subscription_id
            ).execute()
            if response_company.data:
                data_company = response_company.data[0]
            else:
                data_company = []
            ### DATOS EMPRESA - END
                
            generate_report(
                file_name=f"{proof_id}.pdf", 
                data={
                    'data_master': data_master,
                    'data_company': data_company,
                    'last_entry': last_entry,
                    'latest_temperatures_list': latest_temperatures_list,
                    'average_voltage': average_voltage,
                    'leds_mode': leds_mode,
                    'cooler_mode': cooler_mode,
                    'sensor_color_mapping': sensor_color_mapping,
                    'path_base': path_base,
                    'label_leds': label_leds,
                    'iconStatus' : iconStatusProof
                }
            )

            # print('subiendo pdf a supabase')
            path_supabase = subscription_id + '/' + proof_id

            # Si el pdf ya existe lo borramos
            supabase.storage.from_('certificates').remove(path_supabase)

            # Subir PDF a supabase
            with open(path_output, 'rb') as file_name:
                supabase.storage.from_('certificates').upload(
                    path=path_supabase,
                    file=file_name,
                    file_options={"content-type": "application/pdf"}
                )

            # Borrar imagenes de la api qr / plot / pdf cuando este en PRODUCCION
            DEBUG = os.getenv('DEBUG')
            if DEBUG == 'False':
                qr_folder = os.path.join(settings.MEDIA_ROOT, 'data/qr')
                plot_folder = os.path.join(settings.MEDIA_ROOT, 'data/plot')
                pdf_folder = os.path.join(settings.MEDIA_ROOT, 'data/pdf')

                clear_folder(qr_folder)
                clear_folder(plot_folder)
                clear_folder(pdf_folder)
                
            # Generar Response
            status_resp = 'success'
            code = status.HTTP_200_OK
            message = 'PDF generado correctamente!'
            data = ''
            
        except Exception as e:
            status_resp = 'error'
            code = status.HTTP_404_NOT_FOUND
            message = str(e)
            data = []

        return Response({
            'status': status_resp,
            'code': code,
            'message': message,
            'data': data
        })