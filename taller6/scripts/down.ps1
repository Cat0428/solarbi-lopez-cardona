<#
  Taller 6 · Elimina TODA la solución con un solo comando: borra el clúster kind
  (pods, volúmenes y datos de PostgreSQL incluidos). La capa Bronze en data/bronze no se toca.
      .\scripts\down.ps1
#>
kind delete cluster --name microrred
