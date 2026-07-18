"""
SCRIPT DE POBLADO DE CAFETERIA
Ejecutar desde la raiz del proyecto Django:
    python poblar_cafeteria.py

Requiere que las migraciones ya esten aplicadas (python manage.py migrate)
"""
import os
import sys
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cafe_tpv.settings')
django.setup()

from tpv.models import (
    CategoriaProducto, Articulo, InsumoMateriaPrima, ComposicionReceta
)

def poblar():
    print("=== POBLANDO BASE DE DATOS DE CAFETERIA ===\n")

    # --- INSUMOS ---
    insumos_data = [
        ('Cafe en graos', Decimal('5000'), Decimal('500'), 'g'),
        ('Leche entera', Decimal('10000'), Decimal('1000'), 'ml'),
        ('Leche desnatada', Decimal('5000'), Decimal('500'), 'ml'),
        ('Azucar', Decimal('3000'), Decimal('300'), 'g'),
        ('Chocolate en polvo', Decimal('1500'), Decimal('200'), 'g'),
        ('Te verde', Decimal('200'), Decimal('20'), 'ud'),
        ('Te negro', Decimal('200'), Decimal('20'), 'ud'),
        ('Hojaldrados', Decimal('60'), Decimal('10'), 'ud'),
        ('Pan de molde', Decimal('100'), Decimal('10'), 'ud'),
        ('Jamon serrano', Decimal('500'), Decimal('50'), 'g'),
        ('Queso manchego', Decimal('500'), Decimal('50'), 'g'),
        ('Mantequilla', Decimal('500'), Decimal('50'), 'g'),
        ('Nata montada', Decimal('1000'), Decimal('100'), 'ml'),
        ('Licor Baileys', Decimal('500'), Decimal('50'), 'ml'),
        ('Hielo', Decimal('3000'), Decimal('200'), 'g'),
        ('Zumo de naranja', Decimal('2000'), Decimal('200'), 'ml'),
        ('Harina', Decimal('2000'), Decimal('200'), 'g'),
        ('Huevos', Decimal('30'), Decimal('6'), 'ud'),
    ]

    insumos = {}
    for nombre, cantidad, minima, unidad in insumos_data:
        obj, _ = InsumoMateriaPrima.objects.get_or_create(
            nombre=nombre,
            defaults={'cantidad_actual': cantidad, 'cantidad_minima': minima, 'unidad_medida': unidad}
        )
        insumos[nombre] = obj
    print(f"  Insumos: {len(insumos)} OK")

    # --- CATEGORIAS ---
    cats_data = [
        ('Calientes', '\u2615'),
        ('Frias', '\U0001F9CA'),
        ('Bocadillos', '\U0001F96A'),
        ('Pasteleria', '\U0001F950'),
        ('Licores', '\U0001F943'),
    ]

    cats = {}
    for nombre, icono in cats_data:
        obj, _ = CategoriaProducto.objects.get_or_create(
            nombre=nombre, defaults={'icono': icono}
        )
        cats[nombre] = obj
    print(f"  Categorias: {len(cats)} OK")

    # --- ARTICULOS ---
    articulos_data = [
        ('Cafe Solo', Decimal('0.80'), '10.00', 'Calientes', [
            ('Cafe en graos', Decimal('8')),
        ]),
        ('Cafe con Leche', Decimal('1.10'), '10.00', 'Calientes', [
            ('Cafe en graos', Decimal('8')),
            ('Leche entera', Decimal('200')),
        ]),
        ('Cortado', Decimal('1.00'), '10.00', 'Calientes', [
            ('Cafe en graos', Decimal('8')),
            ('Leche entera', Decimal('50')),
        ]),
        ('Capuchino', Decimal('1.50'), '10.00', 'Calientes', [
            ('Cafe en graos', Decimal('8')),
            ('Leche entera', Decimal('250')),
            ('Chocolate en polvo', Decimal('5')),
        ]),
        ('Chocolate Caliente', Decimal('1.60'), '10.00', 'Calientes', [
            ('Leche entera', Decimal('300')),
            ('Chocolate en polvo', Decimal('25')),
        ]),
        ('Te Verde', Decimal('1.00'), '10.00', 'Calientes', [
            ('Te verde', Decimal('1')),
        ]),
        ('Te Negro', Decimal('1.00'), '10.00', 'Calientes', [
            ('Te negro', Decimal('1')),
        ]),
        ('Cafe Frio', Decimal('1.80'), '10.00', 'Frias', [
            ('Cafe en graos', Decimal('8')),
            ('Leche entera', Decimal('150')),
            ('Hielo', Decimal('100')),
        ]),
        ('Capuchino Frio', Decimal('2.20'), '10.00', 'Frias', [
            ('Cafe en graos', Decimal('8')),
            ('Leche entera', Decimal('200')),
            ('Hielo', Decimal('80')),
            ('Chocolate en polvo', Decimal('5')),
        ]),
        ('Zumo de Naranja', Decimal('1.80'), '10.00', 'Frias', [
            ('Zumo de naranja', Decimal('250')),
        ]),
        ('Agua Mineral', Decimal('0.80'), '4.00', 'Frias', []),
        ('Bocadillo Jamon', Decimal('2.50'), '10.00', 'Bocadillos', [
            ('Pan de molde', Decimal('2')),
            ('Jamon serrano', Decimal('60')),
            ('Mantequilla', Decimal('5')),
        ]),
        ('Bocadillo Queso', Decimal('2.20'), '10.00', 'Bocadillos', [
            ('Pan de molde', Decimal('2')),
            ('Queso manchego', Decimal('50')),
            ('Mantequilla', Decimal('5')),
        ]),
        ('Bocadillo Mixto', Decimal('2.80'), '10.00', 'Bocadillos', [
            ('Pan de molde', Decimal('2')),
            ('Jamon serrano', Decimal('40')),
            ('Queso manchego', Decimal('30')),
            ('Mantequilla', Decimal('5')),
        ]),
        ('Croissant', Decimal('1.20'), '10.00', 'Pasteleria', [
            ('Hojaldrados', Decimal('1')),
            ('Mantequilla', Decimal('10')),
        ]),
        ('Napolitana Chocolate', Decimal('1.50'), '10.00', 'Pasteleria', [
            ('Hojaldrados', Decimal('1')),
            ('Chocolate en polvo', Decimal('15')),
            ('Azucar', Decimal('10')),
        ]),
        ('Ensaimada', Decimal('1.30'), '10.00', 'Pasteleria', [
            ('Harina', Decimal('50')),
            ('Azucar', Decimal('15')),
            ('Huevos', Decimal('1')),
        ]),
        ('Baileys', Decimal('2.50'), '21.00', 'Licores', [
            ('Licor Baileys', Decimal('40')),
            ('Hielo', Decimal('50')),
        ]),
        ('Cafe con Baileys', Decimal('3.00'), '21.00', 'Licores', [
            ('Cafe en graos', Decimal('8')),
            ('Leche entera', Decimal('100')),
            ('Licor Baileys', Decimal('30')),
        ]),
    ]

    nuevos = 0
    for nombre, precio, iva, cat_nombre, receta in articulos_data:
        articulo, created = Articulo.objects.get_or_create(
            nombre=nombre,
            defaults={
                'precio_sin_iva': precio,
                'tipo_iva': iva,
                'categoria': cats[cat_nombre],
                'activo': True,
            }
        )
        if created:
            nuevos += 1
            for insumo_nombre, cantidad in receta:
                if insumo_nombre in insumos:
                    ComposicionReceta.objects.get_or_create(
                        articulo=articulo,
                        insumo=insumos[insumo_nombre],
                        defaults={'cantidad_consumida': cantidad}
                    )

    print(f"  Articulos: {nuevos} nuevos de {len(articulos_data)} totales")
    print(f"\n  RESUMEN: {CategoriaProducto.objects.count()} categorias, "
          f"{Articulo.objects.count()} articulos, "
          f"{InsumoMateriaPrima.objects.count()} insumos")
    print("=== LISTO ===")


if __name__ == '__main__':
    poblar()
