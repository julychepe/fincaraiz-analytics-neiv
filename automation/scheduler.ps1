# Script de automatización semanal para el Cron / Task Scheduler
$ProjectDir = "C:\Users\ACER\fincaraiz_analytics"
$LogFile = "$ProjectDir\outputs\automation_trigger.log"

echo "=========================================================" >> $LogFile
echo "? Disparador automático iniciado: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" >> $LogFile

try {
    # 1. Navegar al directorio del proyecto
    cd $ProjectDir
    
    # 2. Ejecutar el pipeline unificado con el Python del sistema
    & "C:\Users\ACER\AppData\Local\Programs\Python\Python314\python.exe" main_pipeline.py >> $LogFile 2>&1
    
    echo "? Pipeline ejecutado por el Scheduler con éxito." >> $LogFile
} catch {
    echo "? ERROR CRÍTICO: No se pudo iniciar el pipeline. Detalle: $_" >> $LogFile
}
echo "=========================================================" >> $LogFile
