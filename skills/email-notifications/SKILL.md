---
name: email-notifications
description: >-
  Guía para implementar notificaciones transaccionales por email en Django con
  Google Workspace SMTP. Incluye configuración del servidor SMTP, diseño de
  plantillas HTML con estilos 100% inline para compatibilidad con Gmail/Outlook,
  resiliencia defensiva ante fallos de socket, correos de confirmación al cliente
  y alertas internas al equipo, con todas las lecciones aprendidas en FOBANDOR.
  Usar cuando se implementa o depura un envío de email transaccional, correo de
  verificación, alerta interna, o se diagnostica un fallo SMTP en producción.
---

# Email Notifications — Lecciones Aprendidas FOBANDOR

## Stack de Email Validado

| Componente | Valor |
|:---|:---|
| Provider SMTP | Google Workspace (`smtp.gmail.com:587 TLS`) |
| Auth | App Password de 16 caracteres (no contraseña de cuenta) |
| Backend Django | `django.core.mail.backends.smtp.EmailBackend` |
| Plantillas | HTML + TXT plano (bilingüe ES/EN) |
| Disparador | `handle_invoice_paid` en `billing/services.py` |

---

## Configuración SMTP Google Workspace

```python
# settings/production.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='FOBANDOR <admin@fobandor.com>')
```

**Generar App Password:**
1. `myaccount.google.com` → Seguridad → Verificación en 2 pasos (activar).
2. `myaccount.google.com/apppasswords` → Crear app password para "Django".
3. Copiar los 16 caracteres sin espacios.

> [!CAUTION]
> Las variables SMTP deben estar inyectadas **en el servicio Docker Swarm**, no solo en
> la UI de EasyPanel. Verificar: `docker service inspect fobandor_web | grep -A30 Env`

---

## Resiliencia Defensiva (Never 500 to User)

```python
# fobandor/users/adapters.py — CustomAccountAdapter
def send_mail(self, template_prefix, email, context):
    """Nunca propagar errores SMTP al usuario: HTTP 500 es inaceptable."""
    try:
        super().send_mail(template_prefix, email, context)
    except (smtplib.SMTPException, OSError, ConnectionError) as exc:
        logger.error("SMTP error al enviar a %s: %s", email, exc)
        # El usuario continúa sin un HTTP 500

# billing/services.py — En handlers de webhook
def send_customer_purchase_email(user, invoice, plan):
    try:
        send_mail(
            subject=f'¡Gracias por tu compra! — {plan.name_es}',
            message=render_to_string('billing/email/customer_purchase_invoice.txt', ctx),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=render_to_string('billing/email/customer_purchase_invoice.html', ctx),
            fail_silently=False,
        )
    except Exception:
        logger.exception("Error enviando email de compra al cliente %s", user.email)
        # No relanzar: el webhook Stripe debe recibir 200 siempre
```

---

## Reglas de Diseño de Plantillas HTML para Email

> [!IMPORTANT]
> Gmail descarta bloques `<style>` y pseudo-clases CSS (`:first-child`, `:last-child`).
> **Todo estilo debe estar inline en cada elemento.**

### Plantilla de Alerta Interna — Patrón "Menos es más"

```html
<!-- templates/billing/email/internal_purchase_alert.html -->
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0; padding:0; font-family: Arial, sans-serif; background-color: #f1f5f9;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr>
      <td style="padding: 20px;">
        <table width="600" align="center" style="background:#ffffff; border-radius:8px; overflow:hidden;">

          <!-- HEADER -->
          <tr>
            <td style="background:#1e40af; color:#ffffff; padding:16px 20px; font-size:12px; font-weight:600; text-transform:uppercase; letter-spacing:1px;">
              NOTIFICACIÓN OPERATIVA SLA
            </td>
          </tr>

          <!-- TÍTULO -->
          <tr>
            <td style="padding:20px; font-size:20px; font-weight:700; color:#0f172a;">
              Nueva Compra de Servicios Registrada
            </td>
          </tr>

          <!-- DATOS — INLINE en cada TD -->
          <tr>
            <td style="padding:0 20px 20px;">
              <table width="100%" style="border-collapse:collapse;">
                <tr>
                  <td style="padding:10px; border-bottom:1px solid #e2e8f0; font-weight:600; color:#0f172a; width:40%;">Cliente</td>
                  <td style="padding:10px; border-bottom:1px solid #e2e8f0; color:#334155;">{{ user.email }}</td>
                </tr>
                <tr>
                  <td style="padding:10px; border-bottom:1px solid #e2e8f0; font-weight:600; color:#0f172a;">Plan</td>
                  <td style="padding:10px; border-bottom:1px solid #e2e8f0; color:#334155;">{{ plan_name }}</td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- CTA -->
          <tr>
            <td style="padding:0 20px 24px; text-align:center;">
              <a href="{{ backoffice_url }}"
                 style="display:inline-block; background:#ea580c; color:#ffffff; padding:12px 28px; border-radius:6px; text-decoration:none; font-weight:700; font-size:14px;">
                Gestionar Orden en Backoffice SLA
              </a>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
```

**Lección crítica (Etapa 11):** Gmail aplica `color: black` al texto si no hay `color` inline. Fondo oscuro + texto negro = ilegible. Usar fondo claro (`#f1f5f9`) o especificar `color:#ffffff` **en cada `<td>`**.

---

## Asunto del Email — Formato Estandarizado

```python
from datetime import datetime
import pytz

# Siempre en hora de Florida (America/New_York)
ny_tz = pytz.timezone('America/New_York')
now_ny = datetime.now(ny_tz)
fecha_hora_ny = now_ny.strftime('%Y-%m-%d %H:%M EST')

subject = f"Nueva compra de servicios - {fecha_hora_ny} - {user.email} - {plan.name_es}"
```

---

## Destinatarios de Alerta Interna (Sin Duplicados)

```python
def get_internal_recipients():
    """Staff + Content_Editors sin duplicados."""
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Group

    User = get_user_model()
    staff_emails = set(
        User.objects.filter(is_staff=True, is_active=True).values_list('email', flat=True)
    )
    try:
        editors_group = Group.objects.get(name='Content_Editors')
        editor_emails = set(
            editors_group.user_set.filter(is_active=True).values_list('email', flat=True)
        )
        staff_emails.update(editor_emails)
    except Group.DoesNotExist:
        pass
    return list(staff_emails)
```

---

## URL del Portal del Cliente — Uso de reverse()

> [!CAUTION]
> **Nunca** hardcodear URLs de portal en templates de email.
> La URL `/es/portal/dashboard/` NO existe. La canónica es `/es/mi-cuenta/`.

```python
# INCORRECTO ❌
portal_url = 'https://fobandor.com/es/portal/dashboard/'

# CORRECTO ✅ (en services.py, con el idioma activo)
from django.urls import reverse
portal_url = f"https://fobandor.com{reverse('portal:dashboard')}"
```

---

## Firma del Correo — Patrón "Menos es más"

> [!TIP]
> El texto `NOT_FOUND` que aparece en Gmail no proviene del código: es el campo
> "Cargo/Job Title" de la cuenta de Google Workspace del remitente.
> **Solución:** Actualizar el perfil en Google Admin Console.
> En el template, usar una firma simple y limpia:

```html
<td style="padding:16px 20px; font-size:12px; color:#64748b; text-align:center;">
  FOBANDOR — Build. Ads. Studio. · Soporte: admin@fobandor.com · www.fobandor.com
</td>
```

---

## Checklist de Email Transaccional

- [ ] Variables SMTP inyectadas en Docker Swarm (verificar con `docker service inspect`).
- [ ] App Password generada (no contraseña de cuenta Google).
- [ ] Todos los estilos HTML **inline** en cada `<td>` (compatibilidad Gmail).
- [ ] Fondo claro o `color` explícito en cada celda de texto (evitar texto invisible).
- [ ] `reverse('portal:dashboard')` para URLs dinámicas (nunca hardcoded).
- [ ] Bloque `try/except` en cada envío de email (nunca propagar 500).
- [ ] Asunto en hora `America/New_York` con `pytz`.
- [ ] Destinatarios internos sin duplicados (Staff ∪ Content_Editors).
- [ ] Plantilla TXT alternativa siempre presente junto a la HTML.

## Referencias

- [memory.md §24, §26, §27 — Notificaciones y Hotfixes de Email](../../memory.md)
- [billing/services.py](../../fobandor/billing/services.py)
- [templates/billing/email/](../../templates/billing/email/)
