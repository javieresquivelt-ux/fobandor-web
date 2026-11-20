---
name: formspree-lead-capture
description: >-
  Guía de integración con Formspree.io para captura de leads y formularios de
  diagnóstico comercial asíncronos en Django. Incluye configuración del endpoint
  12-Factor, envío AJAX sin redirección, honeypot anti-spam, y todos los incidentes
  documentados: Formshield activo reteniendo envíos en "pending", reCAPTCHA
  bloqueando AJAX, y extensión de CompanyProfile como singleton de configuración.
  Usar cuando se implementa o depura un formulario de captación de leads.
---

# Formspree Lead Capture — Lecciones Aprendidas FOBANDOR

## Arquitectura Validada

```
Visitante → Alpine.js @submit.prevent → fetch(formspree_endpoint, {Accept: application/json})
         → Formspree.io (Honeypot: _gotcha, Anti-spam desactivado)
         → Email directo a for@fobandor.com
         → Confirmación in-situ (sin redirección)
```

---

## Configuración 12-Factor (Sin Hardcoding)

```python
# config/settings/base.py
FORMSPREE_ENDPOINT = env("FORMSPREE_ENDPOINT", default="")
```

```python
# fobandor/billing/views.py — Inyectar en contexto de vista
class PricingCatalogView(View):
    def get(self, request):
        return render(request, 'billing/pricing.html', {
            'plans': SubscriptionPlan.objects.filter(is_active=True).order_by('order_type'),
            'formspree_endpoint': settings.FORMSPREE_ENDPOINT,
        })
```

**Variables de entorno requeridas:**
```bash
# .env local y en Docker Swarm (EasyPanel)
FORMSPREE_ENDPOINT=https://formspree.io/f/mqpqqggk
```

---

## Configuración Obligatoria en Dashboard de Formspree

> [!CAUTION]
> Para que el envío AJAX con `Accept: application/json` funcione correctamente,
> se deben desactivar **dos opciones** en el dashboard de Formspree:

Ir a **formspree.io** → Formulario `mqpqqggk` → **Settings** → **Spam Protection**:

| Opción | Valor Requerido | Razón |
|:---|:---|:---|
| **reCAPTCHA** | ✅ Desactivado | AJAX con `Accept: application/json` requiere reCAPTCHA desactivado |
| **Formshield** | ✅ Desactivado | Retiene envíos en "pending" sin entregarlos al email destino |

**Protección anti-spam suficiente:** Honeypot `_gotcha` en el formulario.

---

## Incidente: Envíos en Estado "Pending"

> [!WARNING]
> **Síntoma:** El formulario muestra éxito, pero los envíos quedan en "pending" en
> Formspree y no llegan al email. No es "spam", es "pending" sin clasificar.

**Causa:** Formshield (ML anti-spam de Formspree) retiene los envíos antes de entregarlos.

**Solución:** Desactivar Formshield en el dashboard. No requiere cambios de código ni redeploy.

---

## Incidente: Error AJAX — reCAPTCHA Requerido

> [!WARNING]
> **Síntoma:** `fetch()` retorna `{"error": "In order to submit via AJAX, you need to set a custom key or reCAPTCHA must be disabled..."}`

**Solución:** Desactivar reCAPTCHA en Settings → Spam Protection del formulario.

---

## Formulario Completo con Honeypot

```html
<!-- En pricing.html o home.html -->
<form @submit.prevent="submitForm($event)"
      action="{{ formspree_endpoint }}"
      method="POST">

  <!-- HONEYPOT anti-spam — invisible para humanos, trampa para bots -->
  <input type="text"
         name="_gotcha"
         style="display:none"
         tabindex="-1"
         autocomplete="off"
         aria-hidden="true">

  <!-- Metadatos de enrutamiento en Formspree -->
  <input type="hidden" name="_subject" value="{{ company.diag_form_subject }}">

  <!-- Campos reales -->
  <input type="text" name="name" required placeholder="Nombre">
  <input type="email" name="email" required placeholder="Email">
  <textarea name="message" required placeholder="Cuéntanos tu proyecto..."></textarea>

  <button type="submit" :disabled="submitting">
    <span x-show="!submitting">Enviar</span>
    <span x-show="submitting">Enviando diagnóstico...</span>
  </button>
</form>
```

---

## Textos Dinámicos desde CompanyProfile (CMS)

**Decisión Arquitectónica:** No crear un modelo separado para configuración del formulario.
Extender `CompanyProfile` (singleton existente) con 5 campos:

```python
# fobandor/cms/models.py
class CompanyProfile(models.Model):
    # ... campos existentes ...

    # Formulario de Diagnóstico / Contacto
    diag_form_subject = models.CharField(
        max_length=200,
        default='Nuevo Formulario Web - FOBANDOR',
        verbose_name='Asunto del Formulario de Diagnóstico'
    )
    diag_modal_title_es = models.CharField(max_length=200, default='Solicitud enviada')
    diag_modal_title_en = models.CharField(max_length=200, default='Request sent')
    diag_success_msg_es = models.TextField(
        default='Nos contactaremos a la brevedad.',
        verbose_name='Mensaje de Éxito (ES)'
    )
    diag_success_msg_en = models.TextField(
        default='We will get back to you shortly.',
        verbose_name='Success Message (EN)'
    )
```

**En el template:**
```html
<input type="hidden" name="_subject" value="{{ company.diag_form_subject }}">
<!-- ... -->
<p x-show="submitted">{{ company.diag_success_msg_es }}</p>
```

---

## Configuración Recomendada Formspree (Resumen)

| Setting | Valor |
|:---|:---|
| Email Destino | `for@fobandor.com` (verificado en Account → Linked Emails) |
| reCAPTCHA | ✅ Desactivado |
| Formshield | ✅ Desactivado |
| Honeypot `_gotcha` | ✅ Activo (en el formulario HTML) |
| Notificaciones | Activadas hacia email verificado |

---

## Checklist Formspree

- [ ] `FORMSPREE_ENDPOINT` en `.env` y en Docker Swarm (nunca hardcodeado en templates).
- [ ] reCAPTCHA desactivado en Formspree dashboard.
- [ ] Formshield desactivado en Formspree dashboard.
- [ ] Honeypot `_gotcha` con `style="display:none"` y `tabindex="-1"`.
- [ ] `_subject` dinámico desde `company.diag_form_subject`.
- [ ] Estado Alpine.js: `submitting`, `submitted`, `error` para feedback UX.
- [ ] Email destino verificado en "Account → Linked Emails" en Formspree.

## Referencias

- [memory.md §16 — Integración Formspree](../../memory.md)
- [memory.md §20 — Incidente Formshield "Pending"](../../memory.md)
- [memory.md §17 — CompanyProfile Extensión CMS](../../memory.md)
