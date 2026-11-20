---
name: frontend-tailwind-alpine
description: >-
  Guía de implementación de frontend con Tailwind CSS 3.4+, Alpine.js y HTMX
  para proyectos Django Server-Driven. Incluye configuración de dark mode,
  selector interactivo de planes, corrección de contraste en inputs para Gmail/Chromium,
  blindaje responsive del navbar móvil, toggle de idioma 1-clic, y todos los
  hallazgos UX validados en FOBANDOR.
  Usar cuando se implementa o corrige UI, se configura dark mode, se construye
  un componente interactivo Alpine.js, o se diagnostica un problema de contraste.
---

# Frontend Tailwind + Alpine.js — Lecciones Aprendidas FOBANDOR

## Stack Frontend Validado

| Tecnología | Versión | Servicio |
|:---|:---|:---|
| Tailwind CSS | 3.4+ | Local (compilado, no CDN) |
| Alpine.js | 3.14.9 | Local (`static/js/vendor/alpine.min.js`) |
| HTMX | 2.0.4 | Local (`static/js/vendor/htmx.min.js`) |
| Montserrat | WOFF2 variable | Local (`static/fonts/montserrat/`) |

---

## Lección Crítica: Contraste en Inputs (Chromium/Edge Dark Mode)

> [!CAUTION]
> En modo oscuro bajo Chromium/Edge, los `<input>` sin clases CSS explícitas aparecen
> con **fondo blanco nativo** (user-agent stylesheet) y texto blanco heredado de Tailwind.
> Resultado: **texto invisible**.

**Solución — Reglas globales en `@layer base` de `input.css`:**

```css
/* static/css/input.css */
@layer base {
  input[type="text"],
  input[type="email"],
  input[type="password"],
  input[type="tel"],
  input[type="number"],
  input[type="search"],
  textarea,
  select {
    @apply bg-white dark:bg-white/5 text-gray-900 dark:text-gray-100
           border border-gray-300 dark:border-white/10 rounded-md
           focus:outline-none focus:ring-2 focus:ring-orange-500/50;
  }
}
```

**En formularios de allauth (sin clases automáticas):** Aplicar atributo directo en templates:

```html
<!-- templates/account/login.html -->
{{ form.email|add_class:"w-full px-4 py-3 rounded-lg bg-white/5 dark:bg-white/5 text-gray-100 border border-white/10 focus:ring-2 focus:ring-fobandor-orange" }}
```

---

## Selector Interactivo de Planes Alpine.js

```html
<!-- templates/billing/pricing.html -->
<div x-data="{ selectedPlan: '{{ highlighted_plan_slug|default:plans.0.slug }}' }">

  {% for plan in plans %}
  <div
    class="cursor-pointer rounded-2xl border-2 transition-all duration-300 ease-out
           hover:-translate-y-1.5 hover:shadow-2xl hover:shadow-orange-500/15
           hover:border-orange-500/70"
    :class="{
      'border-orange-500 shadow-orange-500/20': selectedPlan === '{{ plan.slug }}',
      'border-white/10': selectedPlan !== '{{ plan.slug }}'
    }"
    @click="selectedPlan = '{{ plan.slug }}'">

    <!-- Botón principal reactivo -->
    <a href="{% url 'billing:checkout' plan.slug %}"
       :class="{
         'bg-fobandor-orange text-white': selectedPlan === '{{ plan.slug }}',
         'border border-white/20 text-white/70': selectedPlan !== '{{ plan.slug }}'
       }"
       class="block w-full py-3 rounded-xl text-center font-bold transition-all">
      Comenzar
    </a>
  </div>
  {% endfor %}
</div>
```

**Principio validado:** `is_highlighted` del CMS preselecciona la tarjeta recomendada, pero el usuario puede seleccionar cualquier otra libremente.

---

## Toggle de Idioma 1-Clic (Pastilla ES/EN)

> [!TIP]
> Reemplazar `<select>` nativo por toggle tipo pill elimina 2 interacciones → 1.
> Mucho mejor UX en móvil.

```html
<!-- templates/partials/navbar.html -->
{% get_current_language as LANGUAGE_CODE %}
<form method="post" action="{% url 'set_language' %}">
  {% csrf_token %}
  <input type="hidden" name="next" value="{{ request.path }}">
  <button type="submit" name="language" value="{% if LANGUAGE_CODE == 'es' %}en{% else %}es{% endif %}"
          class="px-3 py-1.5 rounded-full border border-white/20 text-sm font-semibold
                 hover:border-fobandor-orange hover:text-fobandor-orange transition-colors">
    {% if LANGUAGE_CODE == 'es' %}EN{% else %}ES{% endif %}
  </button>
</form>
```

---

## Blindaje Responsive del Navbar Móvil

> [!WARNING]
> En pantallas 360-390px, múltiples elementos en la barra generan scroll horizontal.
> `overflow-hidden` puede bloquear `position: sticky`.

**Patrón validado:**
```html
<body class="overflow-x-clip">  <!-- clip, NO hidden -->

<nav class="sticky top-0 z-50">
  <!-- Solo: Logo | Toggle Idioma | Hamburger en móvil -->
  <div class="flex items-center justify-between md:hidden">
    <a href="{% url 'core:home' %}"><!-- logo --></a>
    <div class="flex gap-2">
      <!-- Toggle idioma -->
      <!-- Hamburger Alpine.js -->
    </div>
  </div>

  <!-- Drawer móvil — enlaces de sesión AQUÍ, no en la barra -->
  <div x-show="menuOpen" class="md:hidden border-t border-white/10 py-4">
    {% if user.is_authenticated %}
      <a href="{% url 'portal:dashboard' %}">Mi Cuenta</a>
      <a href="{% url 'account_logout' %}">Salir</a>
    {% else %}
      <a href="{% url 'account_login' %}">Iniciar Sesión</a>
    {% endif %}
  </div>
</nav>
```

---

## Enlaces Canónicos en Navbar (Evitar Anclas Rotas)

> [!IMPORTANT]
> Las anclas puras (`#servicios`) fallan cuando el usuario está en `/precios/`.
> Django no sabe qué página sirve esa ancla.

```html
<!-- INCORRECTO ❌ -->
<a href="#servicios">Servicios</a>

<!-- CORRECTO ✅ — URL canónica con ancla -->
<a href="{% url 'core:home' %}#servicios">Servicios</a>
<a href="{% url 'billing:pricing' %}">Precios</a>
```

---

## Formulario Asíncrono Alpine.js + Fetch (Formspree)

```html
<div x-data="{
  submitting: false,
  submitted: false,
  error: false,
  async submitForm(event) {
    this.submitting = true;
    this.error = false;
    const form = event.target;
    const data = new FormData(form);
    try {
      const response = await fetch(form.action, {
        method: 'POST',
        body: data,
        headers: { 'Accept': 'application/json' }
      });
      if (response.ok) {
        this.submitted = true;
      } else {
        this.error = true;
      }
    } catch {
      this.error = true;
    } finally {
      this.submitting = false;
    }
  }
}">
  <form @submit.prevent="submitForm($event)" action="{{ formspree_endpoint }}" method="POST">
    {% csrf_token %}
    <!-- Honeypot anti-spam (nunca mostrar al usuario) -->
    <input type="text" name="_gotcha" style="display:none" tabindex="-1" autocomplete="off" aria-hidden="true">
    <input type="hidden" name="_subject" value="{{ company.diag_form_subject }}">

    <!-- Campos del formulario -->
    <input type="email" name="email" required placeholder="tu@email.com">
    <textarea name="message" required></textarea>

    <div x-show="!submitted">
      <button type="submit" :disabled="submitting" x-text="submitting ? 'Enviando...' : 'Enviar'"></button>
    </div>
    <div x-show="submitted" x-cloak>
      <p>{{ company.diag_success_msg_es }}</p>
    </div>
    <div x-show="error" x-cloak>
      <p>Error. Escríbenos a admin@fobandor.com</p>
    </div>
  </form>
</div>
```

---

## Anti-FOUC (Flash of Unstyled Content) — Dark Mode

```html
<!-- templates/base.html — antes de cualquier CSS -->
<script>
  (function() {
    const theme = localStorage.getItem('theme') ||
      (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    if (theme === 'dark') document.documentElement.classList.add('dark');
  })();
</script>
```

## tailwind.config.js — Paleta Corporativa

```javascript
module.exports = {
  darkMode: 'class',
  content: ['./templates/**/*.html', './fobandor/**/*.py'],
  theme: {
    extend: {
      colors: {
        'fobandor-orange': '#ea580c',
        'fobandor-dark': '#0f172a',
      },
      fontFamily: {
        sans: ['Montserrat', 'sans-serif'],
      }
    }
  }
}
```

---

## Checklist de Frontend

- [ ] `npm ci` (no `npm install`) para builds deterministas.
- [ ] Compilar Tailwind: `npx tailwindcss -i input.css -o output.css --minify`.
- [ ] Verificar que Alpine.js y HTMX se sirven desde `/static/js/vendor/` (no CDN).
- [ ] Reglas `@layer base` para inputs en `input.css` (contraste en dark mode).
- [ ] `overflow-x-clip` en body, no `overflow-x-hidden` (preserva sticky).
- [ ] URLs canónicas absolutas con ancla en navbar (no anclas puras).
- [ ] Script anti-FOUC dark mode antes del `<link>` CSS en `base.html`.
- [ ] Formularios asíncronos con honeypot `_gotcha` y estado reactivo Alpine.js.

## Referencias

- [memory.md §21 — Hallazgos QA Etapa 6](../../memory.md)
- [memory.md §27 — Optimización UX Emails](../../memory.md)
- [static/css/input.css](../../static/css/input.css)
- [templates/billing/pricing.html](../../templates/billing/pricing.html)
