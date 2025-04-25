"""The dxf bound app to determine the total aera of an dxf"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import ezdxf
import ezdxf.document
import ezdxf.entities
import ezdxf.layouts
from PIL import Image, ImageTk


APPROX = 0.001  # mm distance d'approximation
AVAILABLE = ["LINE", "ARC", "LWPOLYLINE", "POLYLINE", "CIRCLE", "ELLIPSE", "SPLINE"]


# --- Utils ---
def resource_path(relative_path):
    """Permet de retrouver le chemin du fichier, même après compilation avec PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class DxfFile:
    """A class wraper of ezdxf document to do the need thing"""

    def __init__(self, filename=None):
        """The dxffile class for opening and treat dxf files"""
        if filename is not None:
            self.open(filename)
        else:
            self.filename = None
            self.unit_conversion_factor = 1  # default
            self.unit = "unknown"

        self.minmax = 0, 0, 0, 0

    def open(self, filename):
        """open the dxf file"""
        self.filename = filename
        self.doc = ezdxf.readfile(filename)
        self.unit, self.unit_conversion_factor = self.determine_unit()

    # --- DXF Processing ---
    def determine_unit(self):
        """return the right unit and giv the convert number to mm"""
        units = self.doc.header.get("$INSUNITS", 0)
        if units == 4:
            return "mm", 1
        elif units == 5:
            return "cm", 10
        elif units == 6:
            return "m", 1000
        else:
            return "unknown", 1

    def bounding_box_entity(self, entity: ezdxf.entities):
        """return the bounding box of an entities"""

        if entity.dxftype() == "LINE":
            points = [entity.dxf.start, entity.dxf.end]
            points = [(x, y) for (x, y, z) in points]
        elif entity.dxftype() == "LWPOLYLINE":
            points = entity.get_points("xy")
        elif entity.dxftype() == "POLYLINE":
            points = [(v.dxf.location.x, v.dxf.location.y) for v in entity.vertices]
        elif entity.dxftype() == "CIRCLE":
            center = entity.dxf.center
            radius = entity.dxf.radius
            return [
                (center.x - radius, center.y - radius),
                (center.x + radius, center.y + radius),
            ]
        elif entity.dxftype() in ["ARC", "ELLIPSE", "SPLINE"]:
            # real point of an ar
            points = entity.flattening(
                APPROX / self.unit_conversion_factor
            )  # APPROXIMATION
            points = [(x, y) for x, y, z in points]

        minx, miny = None, None
        maxx, maxy = None, None

        ## min max algo
        for x, y in points:
            if minx is None or x < minx:
                minx = x
            if maxx is None or x > maxx:
                maxx = x
            if miny is None or y < miny:
                miny = y
            if maxy is None or y > maxy:
                maxy = y

        return (minx, miny), (maxx, maxy)

    def calculate_bounding_box(self):
        """calculate the bounding box of the whole sheet"""
        msp = self.doc.modelspace()

        min_x, min_y, max_x, max_y = None, None, None, None

        for entity in msp:
            if not entity.dxftype() in AVAILABLE:
                continue
            (minx, miny), (maxx, maxy) = self.bounding_box_entity(entity)
            if min_x is None or minx < min_x:
                min_x = minx
            if max_x is None or maxx > max_x:
                max_x = maxx
            if min_y is None or miny < min_y:
                min_y = miny
            if max_y is None or maxy > max_y:
                max_y = maxy

        self.minmax = min_x, min_y, max_x, max_y
        width = (max_x - min_x) * self.unit_conversion_factor
        height = (max_y - min_y) * self.unit_conversion_factor
        surface = width * height

        return width, height, surface, self.unit

    def get_entitys(self):
        """Return all entities by an iterrator"""
        for i in self.doc.modelspace():
            yield i

    def len_entitys(self):
        if self.filename is None:
            return 0
        else:
            return self.doc.modelspace().__len__()


class DrawDxf(tk.Canvas):
    """The class of drawing dxf"""

    def __init__(self, master, doc: DxfFile, *args, **kwargs):
        """Drowing canvas for drowing things"""
        super().__init__(master, *args, **kwargs)
        self.doc = doc
        self.size = 1
        self.config(bg="WHITE")
        self.bind("<Configure>", self.resize_canvas)

    def resize_canvas(self, event: tk.Event):
        """resize canvas with tkinter configure changements"""
        self.plot_canvas()

    def plot_canvas_entity(self, entity, offset):
        """draw a single entity"""
        if entity.dxftype() == "LINE":
            start = entity.dxf.start
            end = entity.dxf.end
            points = [(start.x, start.y), (end.x, end.y)]
        elif entity.dxftype() in ["LWPOLYLINE"]:
            points = entity.get_points("xy")
        elif entity.dxftype() == "POLYLINE":
            points = entity.points_in_wcs()
        elif entity.dxftype() in ["CIRCLE", "ELLIPSE", "SPLINE", "ARC"]:
            points = entity.flattening(APPROX / self.doc.unit_conversion_factor)
            points = [(x, y) for x, y, z in points]

        points = [
            (x * self.size + offset[0], y * self.size + offset[1]) for (x, y) in points
        ]
        self.create_line(points, fill="BLACK", smooth=False)

    def plot_canvas(self):
        """plot all figures"""
        self.delete("all")
        if self.doc.len_entitys() > 0:
            cvsize = self.winfo_width(), self.winfo_height()
            self.size = min(
                cvsize[0] / (self.doc.minmax[2] - self.doc.minmax[0]),
                cvsize[1] / (self.doc.minmax[3] - self.doc.minmax[1]),
            )
            self.size *= 0.95
            center = (self.doc.minmax[0] + self.doc.minmax[2]) / 2, (
                self.doc.minmax[1] + self.doc.minmax[3]
            ) / 2
            wcenter = cvsize[0] / 2, cvsize[1] / 2
            diff = [wc - self.size * c for wc, c in zip(wcenter, center)]

            for entity in self.doc.get_entitys():
                if entity.dxftype() in AVAILABLE:
                    self.plot_canvas_entity(entity, diff)
                else:
                    print(entity.dxftype())
            self.create_rectangle(
                *[self.size * x + diff[i % 2] for i, x in enumerate(self.doc.minmax)],
                outline="GREEN",
                activeoutline="RED",
            )


class App(tk.Tk):
    """The main app class"""

    def __init__(self, *args, **kwargs):
        """init the app"""
        super().__init__(*args, **kwargs)

        self.iconbitmap(
            resource_path("logo_dxf_bound.ico")
        )  # Ajouter une icône personnalisée
        self.title("DXF Bounding Box Calculator")
        self.geometry("1200x600")

        style = ttk.Style()
        style.configure(
            "RoundedButton.TButton",
            font=("Helvetica", 14),
            background="lightblue",
            foreground="black",
            padding=10,
            relief="flat",
        )
        style.configure(
            "RoundedLabel.TLabel",
            font=("Helvetica", 14),
            background="lightblue",
            foreground="black",
            padding=10,
            relief="flat",
        )

        self.configure(bg="lightblue")

        style.map(
            "RoundedButton.TButton",
            background=[("active", "lightblue")],
            relief=[("pressed", "flat")],
        )

        # Boutons principaux

        self.open_multiple_button = ttk.Button(
            self,
            text="Ouvrir fichier .dxf",
            command=self.open_multiple_files,
            style="RoundedButton.TButton",
        )
        self.open_multiple_button.grid(row=1, column=0, sticky=tk.EW)

        self.copy_button = ttk.Button(
            self,
            command=self.copy_results,
            style="RoundedButton.TButton",
        )
        self.copy_end()
        self.copy_button.grid(row=2, column=0, sticky=tk.EW)

        self.reset_button = ttk.Button(
            self,
            text="Réinitialisation des résultats",
            command=self.reset_results,
            style="RoundedButton.TButton",
        )
        self.reset_button.grid(row=3, column=0, sticky=tk.EW)

        self.resultlabel = ttk.Label(
            self, text="No Results" + "\n" * 8, style="RoundedLabel.TLabel"
        )
        self.resultlabel.grid(row=0, column=0, sticky=tk.EW)
        self.canvas = DrawDxf(self, DxfFile())
        self.canvas.grid(row=0, column=1, rowspan=5, sticky=tk.NSEW)

        self.columnconfigure(0)  # , weight=4)
        self.columnconfigure(1, weight=8)
        self.rowconfigure((1, 2, 3), weight=1)
        self.rowconfigure((0, 4), weight=2)

        # Charger et afficher l'image
        try:
            self.original_image = Image.open(resource_path("image_logiciel.png"))
            self.photo = ImageTk.PhotoImage(self.original_image)
            self.image_label = tk.Label(self, image=self.photo, bg="lightblue")
            self.image_label.grid(row=4, column=0, sticky=tk.EW)
            # self.image_label.bind("<Configure>", self.resize_image)
        except Exception as e:
            print(f"Erreur lors du chargement de l'image : {e}")

        # --- Application ---
        self.results = []
        self.doc = None

    def resize_image(self, event: tk.Event):
        """resize the image to addapt it to the needed size"""
        new_width = min(event.width, 400)
        new_height = min(event.height, 190)

        print(new_height, new_width)

        aspect_ratio_image = self.original_image.width / self.original_image.height
        aspect_ratio_window = new_width / new_height

        if aspect_ratio_window > aspect_ratio_image:
            new_width_adjusted = int(new_height * aspect_ratio_image)
            resized_image = self.original_image.resize((new_width_adjusted, new_height))
        else:
            new_height_adjusted = int(new_width / aspect_ratio_image)
            resized_image = self.original_image.resize((new_width, new_height_adjusted))

        self.photo = ImageTk.PhotoImage(resized_image)
        self.image_label.config(image=self.photo)
        # self.image_label.image = self.photo

    def open_multiple_files(self):
        """open and computes multiples files"""
        file_paths = filedialog.askopenfilenames(filetypes=[("DXF files", "*.dxf")])
        if file_paths:
            for file_path in file_paths:
                self.doc = DxfFile(file_path)
                try:
                    width, height, surface, unit = self.doc.calculate_bounding_box()
                    self.results.append(
                        (os.path.basename(file_path), width, height, surface, unit)
                    )
                    self.canvas.doc = self.doc
                    self.canvas.plot_canvas()
                    self.show_results()

                except Exception as e:
                    messagebox.showerror(
                        "Erreur",
                        f"Erreur avec le fichier {os.path.basename(file_path)} : {e}",
                    )

    def reset_results(self):
        """Reset shown results"""
        self.results = []
        self.show_results()

    def copy_results(self):
        total_surface_m2 = sum(result[3] for result in self.results) / 1e6
        self.clipboard_clear()
        self.clipboard_append(f"{total_surface_m2:.4f} m²")
        self.copy_button.config(text="Copié")
        self.after(2000, self.copy_end)

    def copy_end(self):
        self.copy_button.config(text="Copie des résultats", state=tk.NORMAL)

    def show_results(self):
        """Show the result on the result frame"""
        if len(self.results) < 1:
            self.resultlabel.config(text="No results" + "\n" * 8)
        else:
            name, width, height, surface, unit = self.results[-1]
            string = f"Fichier : {name}\n"
            string += f"\tLargeur : {width:.1f} {unit}\n"
            string += f"\tHauteur : {height:.1f} {unit}\n"
            string += f"\tSurface : {surface:.1f} {unit}²\n"

            total_surface = sum(result[3] for result in self.results)
            total_surface_cm2 = total_surface / 100.0  # mm² to cm²
            total_surface_m2 = total_surface / 1e6  # mm² to m²

            string += "Résultat cumulé \n"
            string += f"\tSurface totale : {total_surface:.2f} mm²\n"
            string += f"\tSurface totale en cm² : {total_surface_cm2:.2f} cm²\n"
            string += f"\tSurface totale en m² : {total_surface_m2:.6f} m²"
            self.resultlabel.config(text=string)


# Configuration de la fenêtre principale

if __name__ == "__main__":
    root = App()
    root.mainloop()
