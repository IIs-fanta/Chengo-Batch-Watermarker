import tkinter
import tkinter.filedialog
from tkinter import messagebox
import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ImageDraw, ImageFont
import os
import threading

# --- 主应用窗口定义 ---
class WatermarkApp(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

        self.title("陈狗批量图片加水印工具")
        # 增大初始窗口尺寸并设置最小尺寸
        self.geometry("1200x700")
        self.minsize(1200, 700)  # 设置最小尺寸限制
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # 添加图标设置
        try:
            # 设置窗口左上角图标和任务栏图标
            self.iconbitmap("window.ico")
        except Exception as e:
            print(f"设置图标失败: {e}")

        # --- 界面布局 ---
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # -- 左侧面板 (队列和控制) --
        self.left_panel = ctk.CTkFrame(self.main_frame)
        self.left_panel.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.left_panel.grid_rowconfigure(1, weight=1)
        self.left_panel.grid_columnconfigure(0, weight=1)

        # -- 队列 --
        self.queue_label = ctk.CTkLabel(self.left_panel, text="图片队列 (将文件或文件夹拖拽至此)")
        self.queue_label.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")
        
        self.queue_listbox = tkinter.Listbox(self.left_panel, bg="#2b2b2b", fg="white", selectbackground="#1f6aa5", relief="flat", borderwidth=0)
        self.queue_listbox.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.queue_listbox.drop_target_register(DND_FILES)
        self.queue_listbox.dnd_bind('<<Drop>>', self.add_to_queue)

        # 右键菜单
        self.context_menu = tkinter.Menu(self, tearoff=0)
        self.context_menu.add_command(label="清空队列", command=self.clear_queue)
        self.queue_listbox.bind("<Button-3>", self.show_context_menu)


        # -- 右侧面板 (设置和预览) --
        self.right_panel = ctk.CTkFrame(self.main_frame)
        self.right_panel.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.right_panel.grid_columnconfigure(0, weight=1)

        # -- 水印设置 --
        self.settings_label = ctk.CTkLabel(self.right_panel, text="水印设置", font=ctk.CTkFont(size=16, weight="bold"))
        self.settings_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        # 内容
        self.watermark_text_label = ctk.CTkLabel(self.right_panel, text="水印内容:")
        self.watermark_text_label.grid(row=1, column=0, padx=10, pady=(5,0), sticky="w")
        self.watermark_text = ctk.CTkEntry(self.right_panel, placeholder_text="输入水印文字")
        self.watermark_text.grid(row=2, column=0, padx=10, pady=(0,10), sticky="ew")
        self.watermark_text.bind("<KeyRelease>", self.update_preview)
        self.watermark_text.insert(0, "Your Watermark")

        # 排布
        self.layout_label = ctk.CTkLabel(self.right_panel, text="排布方式:")
        self.layout_label.grid(row=3, column=0, padx=10, pady=(5,0), sticky="w")
        self.layout_mode = tkinter.StringVar(value="斜向排布")
        layouts = ["单个水印", "水平排布", "斜向排布"]
        for i, layout in enumerate(layouts):
            rb = ctk.CTkRadioButton(self.right_panel, text=layout, variable=self.layout_mode, value=layout, command=self.update_preview)
            rb.grid(row=4, column=0, padx=(20 + i*110), pady=(0,10), sticky="w")
            
        # 透明度
        self.opacity_label = ctk.CTkLabel(self.right_panel, text="透明度 (0-255):")
        self.opacity_label.grid(row=5, column=0, padx=10, pady=(5,0), sticky="w")
        self.opacity_slider = ctk.CTkSlider(self.right_panel, from_=0, to=255, command=self.update_preview)
        self.opacity_slider.set(80)
        self.opacity_slider.grid(row=6, column=0, padx=10, pady=(0,10), sticky="ew")

        # 密度
        self.density_label = ctk.CTkLabel(self.right_panel, text="水印密度:")
        self.density_label.grid(row=7, column=0, padx=10, pady=(5,0), sticky="w")
        self.density_slider = ctk.CTkSlider(self.right_panel, from_=50, to=500, command=self.update_preview)
        self.density_slider.set(200)
        self.density_slider.grid(row=8, column=0, padx=10, pady=(0,10), sticky="ew")

        # -- 预览 --
        self.preview_label = ctk.CTkLabel(self.right_panel, text="效果预览", font=ctk.CTkFont(size=16, weight="bold"))
        self.preview_label.grid(row=9, column=0, padx=10, pady=10, sticky="w")
        self.preview_canvas = ctk.CTkCanvas(self.right_panel, width=300, height=200, bg="#1a1a1a", highlightthickness=0)
        self.preview_canvas.grid(row=10, column=0, padx=10, pady=10, sticky="ewns")
        self.right_panel.grid_rowconfigure(10, weight=1)

        # --- 底部操作栏 ---
        self.bottom_frame = ctk.CTkFrame(self)
        self.bottom_frame.grid(row=1, column=0, padx=10, pady=(0,10), sticky="ew")
        self.bottom_frame.grid_columnconfigure(0, weight=1)
        self.bottom_frame.grid_columnconfigure(1, weight=1)
        self.bottom_frame.grid_columnconfigure(2, weight=1)


        # -- 导出设置 --
        # 将标签改为可编辑的输入框
        self.output_path_entry = ctk.CTkEntry(self.bottom_frame, placeholder_text="未选择导出文件夹")
        self.output_path_entry.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        self.output_button = ctk.CTkButton(self.bottom_frame, text="选择文件夹", command=self.select_output_folder)
        self.output_button.grid(row=0, column=1, padx=10, pady=5, sticky="e")
        self.output_folder = ""

        # -- 开始按钮 --
        self.process_button = ctk.CTkButton(self.bottom_frame, text="开始处理", command=self.start_processing)
        self.process_button.grid(row=0, column=2, padx=10, pady=5, sticky="e")
        
        # -- 进度条 --
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.grid(row=2, column=0, padx=10, pady=(0,10), sticky="ew")
        self.progress_bar.set(0)
        self.progress_label = ctk.CTkLabel(self, text="准备就绪")
        self.progress_label.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="w")


        self.update_preview()


    # --- 功能函数 ---
    def add_to_queue(self, event):
        files_str = self.tk.splitlist(event.data)
        for f in files_str:
            if os.path.isdir(f):
                for root, _, files in os.walk(f):
                    for file in files:
                        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                            self.queue_listbox.insert(tkinter.END, os.path.join(root, file))
            elif f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                self.queue_listbox.insert(tkinter.END, f)

    def clear_queue(self):
        self.queue_listbox.delete(0, tkinter.END)

    def show_context_menu(self, event):
        self.context_menu.tk_popup(event.x_root, event.y_root)

    def select_output_folder(self):
        folder = tkinter.filedialog.askdirectory()
        if folder:
            self.output_folder = folder
            self.output_path_entry.delete(0, tkinter.END)
            self.output_path_entry.insert(0, folder)
            
    def update_preview(self, event=None):
        self.preview_canvas.delete("all")
        
        text = self.watermark_text.get()
        if not text:
            return
            
        opacity = int(self.opacity_slider.get())
        density = int(self.density_slider.get())
        layout = self.layout_mode.get()

        font_size = 30
        try:
            font = ImageFont.truetype("msyh.ttc", font_size) # 微软雅黑
        except IOError:
            font = ImageFont.load_default()

        # 创建一个与预览区域大小相同的水印层
        preview_width = self.preview_canvas.winfo_width()
        preview_height = self.preview_canvas.winfo_height()
        if preview_width <= 1 or preview_height <= 1:
            preview_width, preview_height = 400, 300 # 初始值

        watermark_layer = Image.new('RGBA', (preview_width, preview_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark_layer)

        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        color = (255, 255, 255, opacity)

        if layout == "单个水印":
            x = (preview_width - text_width) / 2
            y = (preview_height - text_height) / 2
            draw.text((x, y), text, font=font, fill=color)
        else:
            spacing = density
            if layout == "斜向排布":
                rotated_layer = Image.new('RGBA', (preview_width*2, preview_height*2), (0, 0, 0, 0))
                rotated_draw = ImageDraw.Draw(rotated_layer)
                for x in range(0, rotated_layer.width, text_width + spacing):
                    for y in range(0, rotated_layer.height, text_height + spacing):
                        rotated_draw.text((x, y), text, font=font, fill=color)
                
                rotated_layer = rotated_layer.rotate(30, expand=False)
                
                x_center, y_center = rotated_layer.width / 2, rotated_layer.height / 2
                box = (x_center - preview_width / 2, y_center - preview_height / 2,
                       x_center + preview_width / 2, y_center + preview_height / 2)
                watermark_layer.paste(rotated_layer.crop(box), (0, 0))

            else: # 水平排布
                for x in range(-text_width, preview_width, text_width + spacing):
                    for y in range(0, preview_height, text_height + spacing):
                        draw.text((x, y), text, font=font, fill=color)

        # 将PIL图像转换为Tkinter PhotoImage并在Canvas上显示
        # 使用PIL的ImageTk模块来转换，而不是CTkImage
        from PIL import ImageTk
        self.preview_photo = ImageTk.PhotoImage(image=watermark_layer)
        self.preview_canvas.create_image(0, 0, anchor="nw", image=self.preview_photo)


    def start_processing(self):
        if self.queue_listbox.size() == 0:
            messagebox.showwarning("警告", "图片队列为空！")
            return
        # 从输入框获取路径
        self.output_folder = self.output_path_entry.get().strip()
        if not self.output_folder or not os.path.isdir(self.output_folder):
            messagebox.showwarning("警告", "请先选择有效的导出文件夹！")
            return
            
        self.process_button.configure(state="disabled")
        self.progress_bar.set(0)
        
        # 使用线程以避免UI冻结
        thread = threading.Thread(target=self.process_images_thread)
        thread.daemon = True
        thread.start()

    def process_images_thread(self):
        images_to_process = self.queue_listbox.get(0, tkinter.END)
        total_images = len(images_to_process)
        
        text = self.watermark_text.get()
        opacity = int(self.opacity_slider.get())
        density = int(self.density_slider.get())
        layout = self.layout_mode.get()
        
        font_size = 40
        try:
            font = ImageFont.truetype("msyh.ttc", font_size) # 微软雅黑, 确保字体文件存在
        except IOError:
            font = ImageFont.load_default()
        
        for i, image_path in enumerate(images_to_process):
            try:
                self.after(0, self.update_progress, i + 1, total_images, os.path.basename(image_path))
                
                base_image = Image.open(image_path).convert("RGBA")
                
                watermark_layer = Image.new('RGBA', base_image.size, (0, 0, 0, 0))
                draw = ImageDraw.Draw(watermark_layer)

                text_bbox = draw.textbbox((0, 0), text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                
                color = (255, 255, 255, opacity)

                if layout == "单个水印":
                    x = (base_image.width - text_width) / 2
                    y = (base_image.height - text_height) / 2
                    draw.text((x, y), text, font=font, fill=color)
                else:
                    spacing = density
                    if layout == "斜向排布":
                        # 在一个更大的画布上绘制，然后旋转裁剪，避免边缘空白
                        w, h = base_image.size
                        diag_len = int((w**2 + h**2)**0.5)
                        rotated_layer = Image.new('RGBA', (diag_len * 2, diag_len * 2), (0,0,0,0))
                        rotated_draw = ImageDraw.Draw(rotated_layer)
                        
                        for x in range(0, rotated_layer.width, text_width + spacing):
                           for y in range(0, rotated_layer.height, text_height + spacing):
                               rotated_draw.text((x, y), text, font=font, fill=color)
                        
                        rotated_layer = rotated_layer.rotate(30, center=(diag_len, diag_len))

                        x_center, y_center = rotated_layer.width/2, rotated_layer.height/2
                        box = (x_center-w/2, y_center-h/2, x_center+w/2, y_center+h/2)
                        watermark_layer.paste(rotated_layer.crop(box), (0,0))

                    else: # 水平排布
                        for x in range(-text_width, base_image.width, text_width + spacing):
                            for y in range(0, base_image.height, text_height + spacing):
                                draw.text((x, y), text, font=font, fill=color)

                # 合成
                final_image = Image.alpha_composite(base_image, watermark_layer).convert("RGB")
                
                # 保存
                filename = os.path.basename(image_path)
                name, ext = os.path.splitext(filename)
                output_filename = f"{name}_watermarked{ext}"
                final_image.save(os.path.join(self.output_folder, output_filename), quality=95) # 对于JPEG, quality=95是高质量

            except Exception as e:
                print(f"处理失败 {image_path}: {e}")
                
        self.after(0, self.processing_finished)

    def update_progress(self, current, total, filename):
        progress = current / total
        self.progress_bar.set(progress)
        self.progress_label.configure(text=f"正在处理: {filename} ({current}/{total})")

    def processing_finished(self):
        self.progress_label.configure(text="处理完成！")
        messagebox.showinfo("成功", f"所有 {self.queue_listbox.size()} 张图片已处理完毕！")
        self.process_button.configure(state="normal")


if __name__ == "__main__":
    # 设置UI主题
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    
    app = WatermarkApp()
    app.mainloop()