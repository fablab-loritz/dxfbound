import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import ezdxf
import matplotlib.pyplot as plt
from PIL import Image, ImageTk


APPROX = 1 #mm distance d'approximation

# --- Utils ---
def resource_path(relative_path):
    """ Permet de retrouver le chemin du fichier, même après compilation avec PyInstaller """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- DXF Processing ---
def determine_unit(doc):
    units = doc.header.get('$INSUNITS', 0)
    if units == 4:
        return 'mm', 1
    elif units == 5:
        return 'cm', 10
    elif units == 6:
        return 'm', 1000
    else:
        return 'unknown', 1

def calculate_bounding_box(file_path):
    doc = ezdxf.readfile(file_path)
    unit, unit_conversion_factor = determine_unit(doc)
    msp = doc.modelspace()

    min_x, min_y, max_x, max_y = None, None, None, None

    for entity in msp:
        points = []
        if entity.dxftype() == 'LINE':
            points = [entity.dxf.start, entity.dxf.end]
        elif entity.dxftype() == 'LWPOLYLINE':
            points = entity.get_points('xy')
        elif entity.dxftype() == 'POLYLINE':
            for v in entity.vertices:
                points.append((v.dxf.location.x, v.dxf.location.y))
        elif entity.dxftype() == 'CIRCLE':
            center = entity.dxf.center
            radius = entity.dxf.radius
            points = [(center.x - radius, center.y - radius), (center.x + radius, center.y + radius)]
        elif entity.dxftype() in ['ARC','ELLIPSE','SPLINE'] : 
            #real point of an ar
            points = entity.flattening(APPROX/unit_conversion_factor)# APPROXIMATION
            points = [(x,y) for x,y,z in points]

        for point in points:
            x, y = point[0], point[1]
            if min_x is None or x < min_x:
                min_x = x
            if min_y is None or y < min_y:
                min_y = y
            if max_x is None or x > max_x:
                max_x = x
            if max_y is None or y > max_y:
                max_y = y

    width = (max_x - min_x) * unit_conversion_factor
    height = (max_y - min_y) * unit_conversion_factor
    surface = width * height

    return width, height, surface, unit

def plot_dxf(file_path):
    doc = ezdxf.readfile(file_path)
    msp = doc.modelspace()

    plt.figure()
    for entity in msp:
        if entity.dxftype() == 'LINE':
            start = entity.dxf.start
            end = entity.dxf.end
            plt.plot([start.x, end.x], [start.y, end.y], 'b-')
        elif entity.dxftype() in ['LWPOLYLINE', 'POLYLINE']:
            points = entity.get_points('xy')
            x_coords, y_coords = zip(*points)
            plt.plot(x_coords, y_coords, 'g-')
        elif entity.dxftype() in ["CIRCLE","ELLIPSE","SPLINE"] :
            points= entity.flattening(2*APPROX)
            points = list(zip(*[(x,y) for x,y,z in points]))
            print(len(points[0]))
            plt.plot(points[0],points[1],"b-")

    plt.gca().set_aspect('equal', adjustable='box')
    plt.show()

# --- Application ---
results = []

def open_single_file():
    file_path = filedialog.askopenfilename(filetypes=[("DXF files", "*.dxf")])
    if file_path:
        try:
            width, height, surface, unit = calculate_bounding_box(file_path)
            surface_cm2 = surface / 100.0  # mm² to cm²
            surface_m2 = surface / 1e6     # mm² to m²

            messagebox.showinfo("Résultat", f"Fichier : {os.path.basename(file_path)}\n\n"
                                            f"Largeur : {width:.2f} {unit}\n"
                                            f"Hauteur : {height:.2f} {unit}\n"
                                            f"Surface : {surface:.2f} {unit}²\n"
                                            f"Surface en cm² : {surface_cm2:.2f} cm²\n"
                                            f"Surface en m² : {surface_m2:.6f} m²")
            plot_dxf(file_path)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'analyser le fichier : {e}")

def open_multiple_files():
    file_paths = filedialog.askopenfilenames(filetypes=[("DXF files", "*.dxf")])
    if file_paths:
        results.clear()
        for file_path in file_paths:
            try:
                width, height, surface, unit = calculate_bounding_box(file_path)
                results.append((width, height, surface, unit))
                messagebox.showinfo("Résultat", f"Fichier : {os.path.basename(file_path)}\n\n"
                                                f"Largeur : {width:.2f} {unit}\n"
                                                f"Hauteur : {height:.2f} {unit}\n"
                                                f"Surface : {surface:.2f} {unit}²")
                plot_dxf(file_path)
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur avec le fichier {os.path.basename(file_path)} : {e}")

def show_cumulative_results():
    if not results:
        messagebox.showinfo("Aucune donnée", "Aucun fichier n'a été analysé.")
        return

    total_surface = sum(result[2] for result in results)
    total_surface_cm2 = total_surface / 100.0  # mm² to cm²
    total_surface_m2 = total_surface / 1e6     # mm² to m²

    messagebox.showinfo("Résultat cumulé", f"Surface totale : {total_surface:.2f} mm²\n"
                                           f"Surface totale en cm² : {total_surface_cm2:.2f} cm²\n"
                                           f"Surface totale en m² : {total_surface_m2:.6f} m²")

def resize_image(event):
    new_width = event.width
    new_height = event.height

    aspect_ratio_image = original_image.width / original_image.height
    aspect_ratio_window = new_width / new_height

    if aspect_ratio_window > aspect_ratio_image:
        new_width_adjusted = int(new_height * aspect_ratio_image)
        resized_image = original_image.resize((new_width_adjusted, new_height), Image.LANCZOS)
    else:
        new_height_adjusted = int(new_width / aspect_ratio_image)
        resized_image = original_image.resize((new_width, new_height_adjusted), Image.LANCZOS)

    photo = ImageTk.PhotoImage(resized_image)
    image_label.config(image=photo)
    image_label.image = photo

# Configuration de la fenêtre principale
root = tk.Tk()
root.iconbitmap(resource_path("logo_dxf_bound.ico"))  # Ajouter une icône personnalisée
root.title("DXF Bounding Box Calculator")
root.geometry("400x410")

style = ttk.Style()
style.configure("RoundedButton.TButton",
                font=("Helvetica", 14),
                background="lightblue",
                foreground="black",
                padding=10,
                relief="flat")
style.map("RoundedButton.TButton",
          background=[("active", "lightblue")],
          relief=[("pressed", "flat")])

# Boutons principaux
open_single_button = ttk.Button(root, text="Choisir un fichier .dxf", command=open_single_file, style="RoundedButton.TButton")
open_single_button.pack(pady=10)

open_multiple_button = ttk.Button(root, text="Choisir plusieurs fichiers .dxf", command=open_multiple_files, style="RoundedButton.TButton")
open_multiple_button.pack(pady=10)

cumulative_button = ttk.Button(root, text="Afficher les résultats cumulés", command=show_cumulative_results, style="RoundedButton.TButton")
cumulative_button.pack(pady=10)

# Charger et afficher l'image
try:
    original_image = Image.open(resource_path("image_logiciel.png"))
    photo = ImageTk.PhotoImage(original_image)
    image_label = tk.Label(root, image=photo)
    image_label.pack(pady=10, expand=True)
    image_label.bind('<Configure>', resize_image)
except Exception as e:
    print(f"Erreur lors du chargement de l'image : {e}")

root.mainloop()
