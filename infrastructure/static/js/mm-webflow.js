function mmWebflow(js) {
    utils = mm.utils;

    function mmListView(js) {
        function ProjectTypeBarChart(el) {
            this.barchart = new mm.BarChart();
            this.el = el;
        }

        ProjectTypeBarChart.prototype = {
            update: function(response) {
                var total_count = response.count;
                var barMap = {
                    "New": 0, "Renewal": 1, "Upgrading": 2, 
                };

                for (key in barMap) {
                    var idx = barMap[key];
                    this.barchart.setupBar($(".vertical-bar_wrapper:eq(" + idx + ")", this.el), key, 0);
                }

                var typeFacet = response.results.facets.type;

                for (idx in typeFacet) {
                    var key = typeFacet[idx]['project_type'];
                    var barID = barMap[key];
                    var count = typeFacet[idx].count;
                    var val = parseInt(count / total_count * 100);
                    var label = key + ": " + val + "%";

                    this.barchart.setupBar($(".vertical-bar_wrapper:eq(" + barID + ")", this.el), label, val);
                }
            }
        };

        function FunctionBarChart(el) {
            this.el = el;
            this.addTooltip(el, "");
        }

        FunctionBarChart.prototype = {
            
            update: function(response) {
                var total_count = response.count;
                var functionFacet = response.results.facets.function;
                var sortedFunctions = functionFacet.sort(function(a, b) {
                    return b.count - a.count;
                });

                var totalBars = 12;

                for (var idx = 0; idx < totalBars; idx++) {
                    if (sortedFunctions[idx] != undefined) {
                        f = sortedFunctions[idx];
                        var label = f['function'];
                        var count = f.count;
                        var val = parseInt(count / total_count * 100);
                        
                        this.setupBar(idx, label, val); 
                    } else {
                        this.setBarHeight(idx, 0);
                    }
                }
            },

            getBar: function(idx) {
                return $(".vertical-bar_wrapper:eq(" + idx + ")", this.el);
            },

            setBarHeight: function(idx, val) {
                var bar = this.getBar(idx);
                $(".bar", bar).css("height", val + "%");
            },

            setupBar: function(idx, text, val) {
                var self = this;
                var label = text + ": " + val + "%";
                var bar = this.getBar(idx);
                this.setBarHeight(idx, val);
                //$(".bar", bar).css("height", val + "%")

                bar.on("mousemove", function(e) {
                    $(".text-block-5", self.tooltip).text(label);
                    self.tooltip.show();
                    self.tooltip.css("left", (-77 + idx * 30) + "px");
                })
                .on("mouseout", function() {
                    self.tooltip.hide();
                });
            },

            addTooltip: function(el, text) {
                $(".chart-tooltip", el).remove();
                this.tooltip = $("<div></div>").addClass("chart-tooltip");
                $(".progress-chart_wrapper", el).append(this.tooltip);
                this.tooltip.append($("<div></div>").addClass("div-block-16"));
                this.tooltip.append($("<div></div>").addClass("text-block-5").text(text));
                this.tooltip.css("width", "50%");
                this.tooltip.css("bottom", "unset");
                this.tooltip.css("top", "-20px");
                this.tooltip.css("display", "none");
                this.tooltip.css("visibility", "visible");

            }
        };

        function filterDropdown(el, defaultValue) {
            this.el = el;
            this.listeners = {};
            this.defaultValue = defaultValue;
            this.enabled = true;
    
            this.selectedElement = $(".chart-dropdown_trigger", this.el);
            this.optionContainer = this.el.find("nav.chart-dropdown_list");
            this.dropdownItemTemplate = $(".dropdown-link:first", this.optionContainer).clone();
        }

        filterDropdown.prototype = {
            reset: function() {
                this.setSelected(this.defaultValue);
            },

            setEnabled: function(val) {
                this.enabled = val;
                if (val) {
                    $("div", this.el).css("background-color", "");
                } else {
                    $("div", this.el).css("background-color", "#f7f7f7");
                }
            },

            clearOptions: function() {
                $(this.el).find(".dropdown-link").remove();
            },

            hideOptions: function() {
                this.optionContainer.removeClass("w--open");
            },

            setSelected: function(label) {
                this.selectedElement.find(".text-block").text(label);
            },

            createOption: function(label, ev) {
                var optionElement = this.dropdownItemTemplate.clone();
                var me = this;

                optionElement.click(function() {
                    me.setSelected(label.text);
                    me.hideOptions();
                    ev(label);
                });

                optionElement.find(".search-dropdown_label").text(label.text);
                optionElement.find(".search-dropdown_value").text("");
                if (label.count) {
                    optionElement.find(".search-dropdown_value").text("(" + label.count + ")");
                }

                me.optionContainer.append(optionElement);
            },

            updateDropdown: function(fields, fieldName, plural, field_key) {
                var me = this;

                this.clearOptions();

                this.createOption({text: "All " + plural}, function(payload) {
                    payload.fieldName = fieldName;
                    me.trigger("removefilters", payload);
                });

                fields.forEach(function(option) {
                    option.fieldName = fieldName;
                    option.text = option[field_key];
                    me.createOption(option, function(payload) {
                        me.trigger("selectedoption", payload);
                    });
                });
            },

            on: function(e, func) {
                if (this.listeners[e] == undefined)
                    this.listeners[e] = [];

                this.listeners[e].push(func);
            },

            trigger: function(e, payload) {
                for (idx in this.listeners[e]) {
                    this.listeners[e][idx](payload);
                }
            }

        };

        function Search(baseUrl) {
            this.baseUrl = baseUrl;
            this.selectedFacets = {};
            this.params = new URLSearchParams();
            this.query = "";
            this.order = '-total_forecast_budget';
        }

        Search.prototype = {
            addFacet: function(key, value) {
                this.selectedFacets[key] = value;
            },

            addOrder: function(orderField) {
                this.order = orderField;
            },

            clearFacets: function(key) {
                if (key != undefined) {
                    delete this.selectedFacets[key];
                } else {
                    this.selectedFacets = {};
                }
            },

            addSearch: function(q) {
                this.query = q;
            },

            clearAll: function(key) {
                this.query = "";
                this.clearFacets();
            },

            createUrl: function() {
                this.params = new URLSearchParams();
                if (this.query != "" && this.query != undefined)
                    this.params.set("q", this.query);

                for (key in this.selectedFacets) {
                    var paramValue = this.selectedFacets[key];
                    this.params.append(key, paramValue);
                }
		//hard code the budget phase and fincial year
		this.params.append('budget_phase', 'Budget year');
		this.params.append('financial_year', '2019/2020');

                if (this.order != undefined) {
                    this.params.append("ordering", this.order);
                }

                return this.baseUrl + "?" + this.params.toString();
            }

        };

        function ListView() {
            var me = this;
            this.search = new Search("/api/v1/infrastructure/search/");
            this.searchState = {
                baseLocation: "/api/v1/infrastructure/coordinates/",
                projectsLocation: "/infrastructure/projects/",
                nextUrl: "",
                params: new URLSearchParams(),
                selectedFacets: {},
                map: L.map("map").setView([-30.5595, 22.9375], 4),
                markers: L.markerClusterGroup(),
                noResultsMessage: $("#result-list-container * .w-dyn-empty"), // TODO check this
                loadingSpinner: $(".loading-spinner"),
		mapPointRequest: null,
		projectRequest: null,
		downloadCSV: "/infrastructure/download"
            };

            this.sorter = new mm.Sorter($("#sorting-dropdown"));
            this.sorter.initialize();
            this.sorter.on("sortchanged", function(payload) {
                me.search.addOrder(payload);
		
                triggerSearch();
            });

            this.typeBarChart = new ProjectTypeBarChart($("#project-type-summary-chart"));
            this.functionBarChart = new FunctionBarChart($("#project-function-summary-chart"));

            var removeFilters = function(payload) {
                me.search.clearFacets(payload.fieldName);
            };

	    var updateURLSearch = function(field,value){
		var params = new URLSearchParams();
		for (fieldName in listView.search.selectedFacets) {
                    params.set(fieldName, listView.search.selectedFacets[fieldName]);
		}
		var queryString = params.toString();
		var url = '?'+queryString;
		history.pushState({
		    field:value}, '', url);
	    };

            var addFilter = function(payload) {
		var fieldName = payload.fieldName;
		var textValue = payload.text;
		
                me.search.addFacet(fieldName, textValue);
		updateURLSearch(fieldName, textValue);
		triggerUpdateFilter();
            };


            this.provinceDropDown = new filterDropdown($("#province-dropdown"), "All Provinces");
            this.municipalityDropDown = new filterDropdown($("#municipality-dropdown"), "All Municipalities");
            this.typeDropDown = new filterDropdown($("#type-dropdown"), "All Project Types");
            this.functionDropDown = new filterDropdown($("#functions-dropdown"), "All Functions");

            [this.provinceDropDown, this.municipalityDropDown, this.typeDropDown, this.functionDropDown].forEach(function(dropdown) {
                dropdown.on("removefilters", removeFilters);
                dropdown.on("selectedoption", addFilter);
            });

            $(".clear-filter__text").on("click", function() {
                $("#Infrastructure-Search-Input").val("");
                me.provinceDropDown.reset();
                me.municipalityDropDown.reset();
                me.typeDropDown.reset();
                me.functionDropDown.reset();
                me.search.clearAll();
		history.pushState({}, '','/infrastructure/projects/');
		triggerUpdateFilter();
            });

        } 

        ListView.prototype = {
            initialize: function() {
                this.onPageLoaded();
            },

            clearProjectResults: function() {
                $("#result-list-container .narrow-card_wrapper-2").remove();
            },

	    loadSearchFromUrl: function(queryString){
		this.provinceDropDown.setEnabled(true);
                this.municipalityDropDown.setEnabled(true);
                this.typeDropDown.setEnabled(true);
                this.functionDropDown.setEnabled(true);
		const params = new URLSearchParams(queryString);
		    for (const [key, value] of params){
			listView.search.addFacet(key, value);
			if (key == 'province'){
			    $('#province-dropdown .text-block').text(value);
			}else if (key == 'municipality'){
			    $('#municipality-dropdown .text-block').text(value);
			}else if (key == 'project_type'){
			    $('#type-dropdown .text-block').text(value);
			}else if (key == 'function'){
			    $('#functions-dropdown .text-block').text(value);
			}else if (key == 'q'){
			    $('#Infrastructure-Search-Input').val(value);
			}
			
		    }
		triggerSearch();
	    },

            onLoading: function(clearResults) {
                if (clearResults || clearResults == undefined)
                    this.clearProjectResults();
                $(".search-detail-value--placeholder").show();
                $(".search-detail-amount--placeholder").show();
                $(".search-detail_projects").hide();
                
                this.provinceDropDown.setEnabled(false);
                this.municipalityDropDown.setEnabled(false);
                this.typeDropDown.setEnabled(false);
                this.functionDropDown.setEnabled(false);
            },

            onPageLoaded: function() {
                var me = this;

                mmListView.resultRowTemplate = $("#result-list-container .narrow-card_wrapper-2:first").clone();
                mmListView.resultRowTemplate.find(".narrow-card_icon").remove();

                mmListView.dropdownItemTemplate = $("#province-dropdown * .dropdown-link:first");
                mmListView.dropdownItemTemplate.find(".search-status").remove();
                mmListView.dropdownItemTemplate.find(".search-dropdown_label").text("");

                this.onLoading(); 
                $("#clear-filters-button").on("click", function() {
                    me.searchState.selectedFacets = {};
                });

		const queryString = window.location.search.substring(1);
		if (queryString){
		    this.loadSearchFromUrl(queryString);
		}
            },

	    onUpdateSearchFilter: function(response){
		this.provinceDropDown.setEnabled(true);
                this.municipalityDropDown.setEnabled(true);
                this.typeDropDown.setEnabled(true);
                this.functionDropDown.setEnabled(true);
		this.searchState.noResultsMessage.hide();

		var facets = response.results.facets;
                this.provinceDropDown.updateDropdown(facets.province, "province", "Provinces", 'geography__province_name');
                this.municipalityDropDown.updateDropdown(facets.municipality, "municipality", "Municipalities", "geography__name");
                this.typeDropDown.updateDropdown(facets.type, "project_type", "Project Types", "project_type");
                this.functionDropDown.updateDropdown(facets.function, "function", "Government Functions", 'function');
	    },

            onDataLoaded: function(response) {
                $("#num-matching-projects-field").text("");
                $("#result-list-container .narrow-card_wrapper").remove();

                this.provinceDropDown.setEnabled(true);
                this.municipalityDropDown.setEnabled(true);
                this.typeDropDown.setEnabled(true);
                this.functionDropDown.setEnabled(true);

                this.searchState.noResultsMessage.hide();

                showResults(response);

                this.typeBarChart.update(response);
                this.functionBarChart.update(response);

                var facets = response.results.facets;
                this.provinceDropDown.updateDropdown(facets.province, "province", "Provinces", 'geography__province_name');
                this.municipalityDropDown.updateDropdown(facets.municipality, "municipality", "Municipalities", "geography__name");
                this.typeDropDown.updateDropdown(facets.type, "project_type", "Project Types", "project_type");
                this.functionDropDown.updateDropdown(facets.function, "function", "Government Functions", 'function');

                // TODO Hack to ensure unit is on the same line as the value
                $(".search-detail__amount").css("display", "flex");
                $(".search-detail-value").css("display", "flex");

                $(".search-detail_projects").show();
                $(".search-detail__amount").show();
                $(".search-detail-value--placeholder").hide();
                $(".search-detail-amount--placeholder").hide();
		$(".dropdown-link").removeClass('active');
            }
        };

    
        var listView = new ListView();
        listView.initialize();

        createTileLayer().addTo(listView.searchState.map);
        listView.searchState.map.addLayer(listView.searchState.markers);

        function buildProjectUrl(project) {
            return listView.searchState.projectsLocation + project.id;
        }

        function createTileLayer() {
            return L.tileLayer('//{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>',
                maxZoom: 18,
                subdomains: 'abc',
            });
        }


        function updateFreeTextParam() {
            listView.searchState.params.set("search", $("#Infrastructure-Search-Input").val());
        }

        function updateFacetParam() {
            listView.searchState.params.delete("selected_facets");
            for (fieldName in listView.searchState.selectedFacets) {
                var paramValue = fieldName + "_exact:" + listView.searchState.selectedFacets[fieldName];
                listView.searchState.params.append("selected_facets", paramValue);
            }
        }

        function buildAllCoordinatesSearchURL() {
            var params = new URLSearchParams();
	    var budget_phase = "Budget year";
            var financial_year = "2019/2020";
            params.set("q", $("#Infrastructure-Search-Input").val());
	    params.set('budget_phase',budget_phase);
	    params.set('financial_year', financial_year);
            for (fieldName in listView.search.selectedFacets) {
                params.set(fieldName, listView.search.selectedFacets[fieldName]);
            }
            return listView.searchState.baseLocation + "?" + params.toString();
        }

        function normaliseResponse(response) {
            var facets = response.results.facets;

            ["province", "municipality", "type", "function"].forEach(function(el) {
                var facet = facets[el];
                facet.forEach(function(el2) {
                    el2.label = el2.key;
                });
            });

            response.results.projects.forEach(function(project) {
                var current_year = new Date().getFullYear();

                // TODO figure out where to put these
                var budget_phase = "Budget year";
                project.total_forecast_budget = 0;

                if (project.expenditure.length > 0) {
                    // Get the most recent year only
                    for (var i = current_year; i >= 2019; i--) {
                        var expenditures = project.expenditure.filter(function(exp) {
                            var budget = exp.financial_year.budget_year == get_year(i);
                            if (budget == true) {i=0}
                            return budget;
                        });
                    }

                    expenditures = expenditures.filter(function(exp) {
                        return exp.budget_phase.name == budget_phase; 
                    });

                    if (expenditures.length > 0)
                        project.total_forecast_budget = expenditures[0].amount;
                }

            });

            return response;
        }

        function get_year(year) {
            var temp_year = year + "/" + (year + 1);
            return temp_year;
        }

        function triggerSearch(url, clearProjects) {
            listView.onLoading(clearProjects);
	    if (listView.searchState.mapPointRequest !== null){
		listView.searchState.mapPointRequest.abort();
	    }
            var isEvent = (url != undefined && url.type != undefined);
            if (isEvent || url == undefined)
                url = listView.search.createUrl();

            listView.searchState.projectRequest = $.get(url)
                .done(function(response) {
                    response = normaliseResponse(response);
                    listView.searchState.nextUrl = response.next;
                    listView.onDataLoaded(response);
                })
                .fail(function(jqXHR, textStatus, errorThrown) {
                    alert("Something went wrong when searching. Please try again.");
                    console.error( jqXHR, textStatus, errorThrown );
                });
            resetMapPoints();
            getMapPoints(buildAllCoordinatesSearchURL());
        }

	function triggerDownload(){
	    var params = new URLSearchParams();
	    var budget_phase = "Budget year";
            var financial_year = "2019/2020";
	    params.set('budget_phase',budget_phase);
	    params.set('financial_year', financial_year);
	    for (fieldName in listView.search.selectedFacets) {
                params.set(fieldName, listView.search.selectedFacets[fieldName]);
            }
	    return listView.searchState.downloadCSV + "?" + params.toString();
	}

	function triggerUpdateFilter(){
	    var url = listView.search.createUrl();
	    
	    listView.searchState.projectRequest = $.get(url)
		.done(function(response){
		    response = normaliseResponse(response);
		    listView.onUpdateSearchFilter(response);
		}).fail(function(jqXHR, textStatus, errorThrown){
		    alert("Something went wrong when searching. Please try again.");
                    console.error( jqXHR, textStatus, errorThrown );
		});
	    
	}

        function getMapPoints(url, resetBounds) {
            var DONT_RESET_BOUNDS = false;
            var RESET_BOUNDS = true;
            resetBounds = resetBounds == undefined ? RESET_BOUNDS : resetBounds;
            listView.searchState.loadingSpinner.show();
            listView.searchState.mapPointRequest = $.get(url)
                .done(function(response) {
                    addMapPoints(response, resetBounds);
                    if (response.next) {
                        getMapPoints(response.next, DONT_RESET_BOUNDS);
                    } else {
                        listView.searchState.loadingSpinner.hide();
                    }
                })
                .fail(function(jqXHR, textStatus, errorThrown) {
		    if (textStatus !== 'abort'){
			alert("Something went wrong when loading map data. Please try again.");
			console.error( jqXHR, textStatus, errorThrown );
		    }
                });
        }

        function showResults(response) {
            $("#num-matching-projects-field").text(utils.formatNumber(response.count));
            $("#search-total-forecast").text(utils.formatHuman(response.results.aggregations.total));
            $(".search-detail__amount .units-label").text(utils.formatUnits(response.results.aggregations.total));
            var resultItem = mmListView.resultRowTemplate.clone();

            if (response.results.projects.length) {
                listView.clearProjectResults();
                listView.searchState.noResultsMessage.hide();
                response.results.projects.forEach(function(project) {
                    var resultItem = mmListView.resultRowTemplate.clone();
                    resultItem.attr("href", buildProjectUrl(project));
                    resultItem.find(".narrow-card_title-2").html(project.project_description);
                    resultItem.find(".narrow-card_middle-column-2:first div").html(project.function);
                    resultItem.find(".narrow-card_middle-column-2:last").html(project.project_type);
                    var amount = "R" + utils.formatNumber(project.total_forecast_budget, true);
                    resultItem.find(".narrow-card_last-column-2").html(amount);
                    $("#result-list-container").append(resultItem);
                });
		if (!response.next){
		    $(".load-more_wrapper").hide();
		}
            } else {
                listView.searchState.noResultsMessage.show();
            }
        }

        function resetMapPoints() {
            listView.searchState.markers.clearLayers();
        }

        function addMapPoints(response, resetBounds) {
            var markers = [];
            response.results.forEach(function(project) {
                if (! project.latitude || ! project.longitude)
                    return;

                var latitude = parseFloat(project.latitude);
                if (latitude < -34.5916 || latitude > -21.783733) {
                    //console.log("Ignoring latitude " + latitude);
                    return;
                }

                var longitude = parseFloat(project.longitude);
                if (longitude < 14.206737 || longitude > 33.074960) {
                    //console.log("Ignoring longitude " + longitude);
                    return;
                }
		var budget_phase = "Budget year";
		var financial_year = "2019/2020";
		var expenditures;
		if (project.expenditure.length > 0) {
                    expenditures = project.expenditure.filter(function(exp) {
                        return exp.financial_year.budget_year == financial_year;
                    });
		    
                    expenditures = expenditures.filter(function(exp) {
                        return exp.budget_phase.name == budget_phase; 
                    });
                    // if (expenditures.length > 0)
                    //     project.total_forecast_budget = expenditures[0].amount;
                }
		var markerText = 'not avaliable';
		if (expenditures.length > 0){
		    var units = utils.formatUnits(expenditures[0].amount);
		    var numberFormat = utils.formatHuman(expenditures[0].amount);
		    markerText = project.project_description + '<br><a target="_blank" href="' +
		    buildProjectUrl(project) + '">Jump to project</a></br>' +
		    "<br>" + "Budget: " + numberFormat + units + "</br>";
		}else{
		    markerText = project.project_description + '<br><a target="_blank" href="' +
		    buildProjectUrl(project) + '">Jump to project</a></br>' +
		    "<br>" + "Budget: Not Avaliable" +  + "</br>";
		}


                var marker = L.marker([latitude, longitude])
                    .bindPopup(markerText);
                markers.push(marker);
            });
            if (markers.length) {
                listView.searchState.markers.addLayers(markers);
                listView.searchState.map.fitBounds(listView.searchState.markers.getBounds());
            }
        }

         $("#Infrastructure-Search-Input").keypress(function (e) {
            var key = e.which;
            if (key == 13) {  // the enter key code
                listView.searchState.params.set("q", $("#Infrastructure-Search-Input").val());
                // TODO move this into an object
                var query = $("#Infrastructure-Search-Input").val();
                listView.search.addSearch(query);
                //triggerSearch();
            }
        });
        $("#Search-Button").on("click", function(){
	    listView.search.addFacet("q", $("#Infrastructure-Search-Input").val());
	    triggerSearch();  
	});
	$("#Download-Button").on("click", function(e){
	    //e.preventDefault();
	    var url = triggerDownload();
	    $('#Download-Button').attr('href', url);
	    $(this).click();
	});

        $(".load-more_wrapper a").click(function(e) {
            if (listView.searchState.nextUrl.length > 0) {
                triggerSearch(listView.searchState.nextUrl, false);
            }
        });

        triggerSearch();
    }

    function mmDetailView(js) {

        function setValue(selector, val) {
            if (val == "" || val == undefined)
                return selector
                    .text("Not available")
                .addClass("not-available");
            else
                return selector
                    .text(val)
                .removeClass("not-available");
        }

        function formatCoordinates(latitude, longitude) {
            if (
                latitude != undefined && latitude != 0
                && longitude != undefined && longitude != 0
            )
                return coordinates = latitude + ", " + longitude;
            return "";
        }

        function formatAssetClass(assetClass, assetSubClass) {
            var asset = "";

            if (assetClass != "" && assetClass != undefined)
                asset = assetClass;
            
            if (assetSubClass != "" && assetSubClass != undefined)
                asset += " (" + assetSubClass + ")" ;

            return asset;
        }

        function setMapCoordinates(selector, coords) {
            var url = "https://www.openstreetmap.org/export/embed.html?";
            var params = {
                bbox: coords.join(","),
                layer: "mapnik"
            };
            selector.src = url + $.param(params);
        }

        function createMap(selector, bbox, markers) {
            var map = L.map(selector);

            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                }).addTo(map);

            map.fitBounds([
              [bbox[3], bbox[2]],
              [bbox[1], bbox[0]],
            ]);

            return map;
        }

        function addMarker(map, coords, message) {
            if (coords[0] != undefined && coords[1] != undefined && coords[0] != 0 && coords[1] != 0) {
                var marker = L.marker(coords).addTo(map);

                if (message != undefined) {
                    marker
                        .bindPopup(message)
                        .openPopup();
                }
            }
        }

        // TODO change the budget year label currently hardcoded to specific years in the template
        function setFinanceValue(selector, expenses, phase, budget_year) {
            if (expenses.length == 0)
                return setValue(selector, "");
            else {
                for (var idx in expenses) {
                    var e = expenses[idx];    
                    if (e["budget_phase"] != undefined)
                        if (e["budget_phase"]["name"] == phase && e["financial_year"]['budget_year'] == budget_year)
                            return setValue(selector, utils.formatCurrency(e["amount"]));
                }
                return setValue(selector, "");
            }
        }

        setValue($(".project-description"), js["project_description"]);
        setValue($(".project-number__value"), js["project_number"]);
        
        var classSubclass = formatAssetClass(js["asset_class"], js["asset_subclass"]);
        setValue($(".project-details .asset-class"), classSubclass);

        setValue($(".project-details .function"), js["function"]);
        setValue($(".project-details .mtsf-outcome"), js["mtsf_service_outcome"]);
        setValue($(".project-details .iudf"), js["iudf"]);
        setValue($(".project-details .project-type"), js["project_type"]);

        setValue($(".geography .province, .breadcrumbs .province"), js["geography"]["province_name"]);
        setValue($(".geography .municipality, .breadcrumbs .municipality"), js["geography"]["name"]);
        setValue($(".geography .ward"), js["ward_location"]);
        // TODO remove
        $(".breadcrumbs .home").attr("href", "/infrastructure/projects");
	$(".breadcrumbs .province").attr("href", "/infrastructure/projects?province="+ js["geography"]["province_name"]);
	$(".breadcrumbs .municipality").attr("href", "/infrastructure/projects?province="+ js["geography"]["province_name"]+"&municipality="+ js["geography"]["name"]);
	

        var coordinates = formatCoordinates(js["latitude"], js["longitude"]);
        setValue($(".geography .coordinates"), coordinates);

        setFinanceValue($(".finances .outcome"), js["expenditure"], "Audited Outcome", "2017/2018");
        setFinanceValue($(".finances .forecast"), js["expenditure"], "Full Year Forecast", "2018/2019");

        // TODO take into account the budget year
        setFinanceValue($(".finances .budget1"), js["expenditure"], "Budget year", "2019/2020");
        setFinanceValue($(".finances .budget2"), js["expenditure"], "Budget year", "2020/2021");
        setFinanceValue($(".finances .budget3"), js["expenditure"], "Budget year", "2021/2022");

        //$(".project-map iframe").remove();
        map = createMap("project-map", js["geography"]["bbox"], [[js["latitude"], js["longitude"]]]);
        addMarker(map, [js["latitude"], js["longitude"]], js["project_description"]);

    }

    if (js["view"] == "list")
        mmListView(js);
    else if (js["view"] == "detail")
        mmDetailView(js);
    else
        throw "Could not recognise view - expected list or detail";

}

function filterFunction() {
  var input, filter, ul, li, a, i;
  input = document.getElementById("muniInput");
  filter = input.value.toUpperCase();
  var div = document.getElementById("muniDropdown");
  a = div.getElementsByTagName("a");
  for (i = 0; i < a.length; i++) {
    var txtValue = a[i].textContent || a[i].innerText;
    if (txtValue.toUpperCase().indexOf(filter) > -1) {
      a[i].style.display = "";
    } else {
      a[i].style.display = "none";
    }
  }
} 
