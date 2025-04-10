import tkinter as tk
from tkinter import ttk
import requests
from bs4 import BeautifulSoup
import re
import locale
from screeninfo import get_monitors
import os

# Set locale for number formatting of path cost
locale.setlocale(locale.LC_ALL, '')

# Get screen resolution
monitor = get_monitors()
screen_height = monitor[0].height
screen_width = monitor[0].width
print('screen_height: ' + str(screen_height) + ' screen_width: ' + str(screen_width))

train_stations = []

class RouteFinderGUI:
    def __init__(self, root, force_update):
        self.force_update = force_update
        self.root = root
        self.graph = self.gather_stations()
        self.setup_gui()
    
    def update_train_list_from_wiki(self):
        # Get train connection data from wiki
        if not os.path.isfile('.\\wiki_site.html') or self.force_update:
            url = 'https://underspace.fandom.com/wiki/Train_Travel'
            page = requests.get(url)
            with open('.\\wiki_site.html', 'wb+') as file:
                file.write(page.content)
                file.close()
        
    def setup_gui(self):
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Source selection
        ttk.Label(self.main_frame, text="Source:").grid(row=0, column=0, sticky=tk.E)
        self.source_var = tk.StringVar()
        self.source_combo = ttk.Combobox(self.main_frame, 
                                      textvariable=self.source_var,
                                      values=list(sorted(self.graph.keys())))
        self.source_combo.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        # Destination selection
        ttk.Label(self.main_frame, text="Destination:").grid(row=1, column=0, sticky=tk.E)
        self.dest_var = tk.StringVar()
        self.dest_combo = ttk.Combobox(self.main_frame,
                                     textvariable=self.dest_var,
                                     values=list(sorted(self.graph.keys())))
        self.dest_combo.grid(row=1, column=1, sticky=(tk.W, tk.E))
        
        # Find routes button
        ttk.Button(self.main_frame, text="Find Routes", 
                  command=self.find_routes).grid(row=2, column=0, columnspan=2)
        
        # Results text area
        self.results_text = tk.Text(self.main_frame, height=int(screen_height/32), width=int(screen_height/4))
        self.results_text.grid(row=3, column=0, columnspan=2, pady=10)

    def extract_between(self,text):
        # Regex matching for path cost
        pattern = f"{re.escape('$')}(.*?){re.escape(',')}(.{{3}})"
        matches = re.findall(pattern, text)
        return [match[0] + match[1] for match in matches]
    
    def gather_stations(self):
        # Parse wiki data into searchable dictionary
        self.update_train_list_from_wiki()
        soup = ''
        with open('.\\wiki_site.html', 'rb') as doc:
            soup = BeautifulSoup(doc.read(), 'html.parser')
            doc.close()

        connections_list = {}
        source = ''
        source_station = ''
        dest = ''
        dest_station = ''
        dest_dict = {}

        for i, station_html in enumerate(soup.find_all('td')):
            if i % 3 == 2:
                cost = self.extract_between(str(station_html))
            for j, station in enumerate(station_html.find_all('a')):
                    if i % 3 == 0:
                        source_station = station.get('title')
                    if i % 3 == 1:
                        train_stations.append(station.get('title') + ' - ' + source_station)
                        source = station.get('title') + ' - ' + source_station
                    if i % 3 == 2:
                        if j % 2 == 0:
                            dest_station = station.get('title')
                        if j % 2 == 1:
                                dest = station.get('title') + ' - ' + dest_station
                                dest_dict[dest] = cost[int(j/2)]
            if i % 3 == 2:
                connections_list[source] = dest_dict
                dest_dict = {}
        return connections_list
        
    def find_routes(self):
        source = self.source_var.get()
        dest = self.dest_var.get()
        
        if not source or not dest:
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "Please select both source and destination")
            return
            
        # Find all routes
        routes = self.find_all_routes(self.graph, source, dest)
        
        # Sort by cost and get top 10
        routes = sorted(routes, key=lambda x: x[1])[:10]
        
        # Display results
        self.results_text.delete(1.0, tk.END)
        if len(routes) == 0:
            self.results_text.insert(tk.END, 'No routes found')
        for path, cost in routes:
            self.results_text.insert(tk.END, 
                                   f"Path: {' -> '.join(path)}\nCost: {cost:n} Credits\n\n")
    
    def find_all_routes(self, graph, source, destination):
        # Search for all paths between source and destination
        def dfs(current, path, cost, visited):
            if current == destination:
                all_routes.append((path, cost))
                return
            
            next_destinations = graph.get(current, {})
            for next_dest, edge_cost in next_destinations.items():
                if next_dest not in visited:
                    new_path = path + [next_dest]
                    new_cost = int(cost) + int(edge_cost)
                    new_visited = visited | {current}
                    dfs(next_dest, new_path, new_cost, new_visited)
        
        all_routes = []
        if source in graph:
            dfs(source, [source], 0, set())
        return all_routes  

# Example usage
if __name__ == "__main__":
    # Sample routing graph
    routing_graph = {
        'A': {'B': 2, 'C': 3},
        'B': {'A': 2, 'C': 1, 'D': 4},
        'C': {'A': 3, 'B': 1, 'D': 2},
        'D': {'B': 4, 'C': 2}
    }
    

    root = tk.Tk()
    root.title("Underspace Train Travel Guide")
    app = RouteFinderGUI(root, force_update=False)
    root.mainloop()