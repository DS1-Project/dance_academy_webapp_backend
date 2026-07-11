# Tests manuales — módulo Sales
# Base URL: http://127.0.0.1:8000
# Requisito: servidor corriendo (`python manage.py runserver`) y JWT de un cliente aprobado.

## 0. Login (obtener token)

POST /api/auth/login/
Content-Type: application/json

{
  "email": "cliente@ejemplo.com",
  "password": "TuPassword123",
  "captcha_token": "dev-bypass"
}

Guardar el valor de `access` como TOKEN.

---

## 1. Crear venta (factura pending)

POST /api/sales/
Authorization: Bearer TOKEN
Content-Type: application/json

{
  "choreography_ids": ["UUID-DE-COREOGRAFIA-APROBADA"],
  "billing_address": "Calle 5 #10-20, Cali, Colombia"
}

Esperado: 201
- payment_status = "pending"
- total_amount = suma de actual_price de ChoreographyStat
- details con unit_price por ítem

Verificar en Supabase (Table Editor):
- sales_sale: nueva fila pending
- sales_saledetail: una fila por coreografía

---

## 2. Listar mis ventas

GET /api/sales/
Authorization: Bearer TOKEN

Esperado: 200, solo ventas del cliente autenticado.

---

## 3. Detalle de una venta

GET /api/sales/{SALE_ID}/
Authorization: Bearer TOKEN

Esperado: 200 con details anidados.

---

## 4. Checkout exitoso (simulación de pago)

POST /api/sales/{SALE_ID}/checkout/
Authorization: Bearer TOKEN
Content-Type: application/json

{
  "success": true
}

Esperado: 200
- payment_status = "completed"

Verificar en Supabase:
- sales_sale.payment_status = completed
- sales_enrollment: fila client + choreography
- choreography_choreographystat.total_sales_count incrementado

---

## 5. Checkout fallido

Crear otra venta (paso 1) y luego:

POST /api/sales/{SALE_ID}/checkout/
Authorization: Bearer TOKEN
Content-Type: application/json

{
  "success": false
}

Esperado: 200
- payment_status = "failed"
- sin filas nuevas en sales_enrollment

---

## 6. Mis enrollments

GET /api/sales/my-enrollments/
Authorization: Bearer TOKEN

Esperado: 200 con coreografías compradas tras checkout exitoso.

---

## 7. Casos negativos (rápidos)

- Sin token → 401
- Admin creando venta POST /api/sales/ → 403
- Checkout de venta ajena → 403 o 404
- Checkout de venta ya completed → 400
- Coreografía no aprobada / ya inscrita → 400

---

## PowerShell (ejemplo rápido)

$base = "http://127.0.0.1:8000"
$login = Invoke-RestMethod -Method Post -Uri "$base/api/auth/login/" -ContentType "application/json" -Body '{"email":"cliente@ejemplo.com","password":"TuPassword123","captcha_token":"dev-bypass"}'
$token = $login.access
$headers = @{ Authorization = "Bearer $token" }

$sale = Invoke-RestMethod -Method Post -Uri "$base/api/sales/" -Headers $headers -ContentType "application/json" -Body '{"choreography_ids":["UUID-COREOGRAFIA"],"billing_address":"Calle 5 #10-20, Cali"}'
$sale.id
$sale.payment_status

Invoke-RestMethod -Method Post -Uri "$base/api/sales/$($sale.id)/checkout/" -Headers $headers -ContentType "application/json" -Body '{"success":true}'
