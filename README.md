# Proyecto 3 - Asistente de Escritorio

Este repositorio contiene el sistema para el **Asistente de Escritorio**, un proyecto desarrollado para el curso *CE5507 Modelación Hardware/Software con Orientación a Objetos*. El sistema integra una interfaz gráfica de usuario en HTML (Frontend) conectada de forma inalámbrica mediante sockets TCP/IP en un Backend de Python hacia un dispositivo de hardware basado en Arduino Uno.

## Requisitos Previos

- Python 3.10 o superior instalado en el sistema.
- Git instalado para el control de versiones.

## Guía de Inicialización del Entorno

Siga las instrucciones correspondientes según el sistema operativo de su estación de desarrollo para preparar el entorno virtual e instalar las dependencias requeridas.

### 1. Clonar el repositorio y posicionarse en la raíz

```bash
git clone https://github.com/feli7942/Proyecto-3.git
cd Proyecto-3
```

### 2. Creación del Entorno Virtual (```venv```)

Cree un entorno virtual aislado para evitar conflictos globales de librerías.

```bash
python -m venv venv
```

### 3. Activación del Entorno Virtual

Active el entorno virtual según su sistema operativo:

- En Windows (PowerShell / CMD):

```bash￼
.\venv\Scripts\activate
```

- En Linux / macOS:

```bash
source venv/bin/activate
```

*(Sabrá que se activó correctamente porque verá el indicador ```(venv)``` al inicio de la línea de comandos de su terminal).*

### 4. Instalación de Dependencias

Con el entorno virtual activo, ejecute el gestor de paquetes para instalar de forma automatizada las librerías necesarias especificadas en el archivo de requerimientos:

```bash
pip install -r requeriments.txt
```

## Ejecución de la Aplicación
El proyecto está diseñado bajo un principio de modularidad y control centralizado. Toda la lógica del backend (servidor web y servidor de sockets WiFi) es inicializada y controlada a través del punto de entrada principal ```main.py```.

Para arrancar el sistema completo, ejecute el siguiente comando desde la raíz del proyecto:

```bash 
python src/backend/main.py
```

Ahora abra el navegador web de su preferencia y escriba el siguiente link:

```bash
http://localhost:5000/
```
