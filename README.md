# Proyecto 3 - Asistente de Escritorio

Este repositorio contiene el sistema integral para el **Asistente de Escritorio**, un proyecto desarrollado para el curso *CE5507 Modelación Hardware/Software con Orientación a Objetos*. 

El sistema implementa un entorno ciberfísico que integra una interfaz gráfica de usuario interactiva basada en tecnologías web (Frontend), conectada de forma bidireccional mediante sockets TCP/IP a un Backend central en Python, comunicándose dinámicamente con un dispositivo de hardware simulado o físico (basado en Arduino Uno/ESP8266).

---

## Requisitos Previos

Antes de inicializar la aplicación, asegúrese de contar con los siguientes componentes instalados en su estación de trabajo:
- **Python 3.10 o superior** (configurado en las variables de entorno del sistema).
- **Git** para la gestión y control de versiones.

---

## Preparación Inicial

Abra una terminal en su sistema operativo, clone el repositorio remoto y colóquese en la raíz del proyecto ejecutando:

```bash
git clone [https://github.com/feli7942/Proyecto-3.git](https://github.com/feli7942/Proyecto-3.git)
cd Proyecto-3
```

## Ejecución Automatizada de la Aplicación

El proyecto cuenta con scripts lanzadores de nivel industrial que automatizan por completo la gestión del entorno. Al ejecutar el script correspondiente a su sistema operativo, este realizará las siguientes tareas de manera secuencial:

1. Detectar si existe el entorno virtual (```venv```). Si no se encuentra, lo creará automáticamente.
2. Activar el entorno virtual aislado.
3. Verificar, instalar o actualizar silenciosamente todas las dependencias listadas en el archivo ```requirements.txt```.
4. Levantar de forma asíncrona el navegador web predeterminado apuntando directamente a la interfaz local (```http://localhost:5000```).
5. Inicializar el backend centralizado (```main.py```) para activar el servidor Flask y el servidor de Sockets TCP.

## Instrucciones para Windows

Si utiliza PowerShell o CMD, simplemente ejecute el archivo por lotes ubicado en la raíz:

```bash
.\run.bat
```

## Instrucciones para Linux

Si se encuentra en un entorno Unix, otorgue permisos de ejecución al script de Shell e inicialícelo:

```bash
chmod +x run.sh
.\run.sh
```
