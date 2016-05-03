(function(exports) {
  "use strict";

  // progress indicators
  var spinning = 0;
  function spinnerStart() {
    spinning++;

    // this stops us showing a spinner for cached queries which
    // return very quickly
    _.delay(function() {
      if (spinning > 0) $('#spinner').show();
    }, 200);
  }

  function spinnerStop() {
    spinning--;
    if (spinning === 0) {
      $('#spinner').hide();
    }
  }

  var Filters = Backbone.Model.extend();
  var Cells = Backbone.Model.extend({
    defaults: {
      items: [],
    }
  });
  var State = Backbone.Model.extend({});

  // global municipalities list
  var municipalities;
  var cube = {
    order: 'item.position_in_return_form:asc',
    drilldown: ['demarcation.code', 'demarcation.label', 'item.code', 'item.label', 'item.return_form_structure', 'item.position_in_return_form'],
    model: CUBES[CUBE_NAME].model,
  };
  cube.aggregates = _.map(cube.model.measures, function(m) { return m.ref + '.sum'; });


  /** The filters the user can choose
   */
  var FilterView = Backbone.View.extend({
    el: '.table-controls',
    events: {
      'click .del': 'muniRemoved',
      'click input[name=year]': 'yearChanged',
    },

    initialize: function(opts) {
      this.filters = opts.filters;
      this.filters.on('change', this.render, this);
      this.filters.on('change', this.saveState, this);

      this.state = opts.state;
      this.state.on('change', this.loadState, this);

      this.preload();
      this.loadState();
    },

    loadState: function() {
      // load state from browser history
      this.filters.set({
        municipalities: this.state.get('municipalities') || [],
        year: this.state.get('year'),
      });
    },

    saveState: function() {
      // save global state to browser history
      this.state.set({
        municipalities: this.filters.get('municipalities'),
        year: this.filters.get('year')
      });
    },

    preload: function() {
      var self = this;

      spinnerStart();
      $.get(MUNI_DATA_API + '/cubes/municipalities/facts', function(resp) {
        var munis = _.map(resp.data, function(muni) {
          // change municipality.foo to foo
          _.each(_.keys(muni), function(key) {
            if (key.startsWith("municipality.")) {
              muni[key.substring(13)] = muni[key];
              delete muni[key];
            }
          });
          return muni;
        });

        // global municipalities list
        municipalities = _.indexBy(munis, 'demarcation_code');

        // sanity check pre-loaded municipalities
        self.filters.set('municipalities', _.select(self.filters.get('municipalities'), function(id) {
          return !!municipalities[id];
        }), {silent: true});

        // force a change so we re-render
        self.filters.trigger('change');
      }).always(spinnerStop);

      spinnerStart();
      $.get(MUNI_DATA_API + '/cubes/' + CUBE_NAME + '/members/financial_year_end.year', function(data) {
        self.years = _.pluck(data.data, "financial_year_end.year").sort().reverse();
        self.renderYears();

        // sanity check pre-loaded year
        var year = self.filters.get('year');
        self.filters.set('year', _.contains(self.years, year) ? year : self.years[0], {silent: true});

        // force a change so we re-render
        self.filters.trigger('change');
      }).always(spinnerStop);
    },

    render: function() {
      var $list = this.$('.chosen-munis').empty();
      var munis = this.filters.get('municipalities');
      var self = this;

      if (municipalities && !this.$muniChooser) {
        this.renderMunis();
      }

      // show chosen munis
      if (munis.length === 0) {
        $list.append('<li>').html('<i>Choose a municipality below.</i>');
      } else if (municipalities) {
        _.each(munis, function(muni) {
          muni = municipalities[muni];
          $list.append($('<li>')
            .text(muni.long_name)
            .data('id', muni.demarcation_code)
            .prepend('<a href="#" class="del"><i class="fa fa-times-circle"></i></a> ')
          );
        });
      }

      // ensure year is checked
      var year = (this.filters.get('year') || "").toString();
      this.$('.year-chooser input[name=year]').prop('checked', function() {
        return $(this).val() == year;
      });
    },

    renderMunis: function() {
      function formatMuni(item) {
        if (item.info) {
          return $("<div>" + item.info.name + " (" + item.id + ")<br><i>" + item.info.province_name + "</i></div>");
        } else {
          return item.text;
        }
      }

      // make objects that select2 understands
      var munis = _.map(municipalities, function(muni) {
        return {
          id: muni.demarcation_code,
          text: muni.long_name + " " + muni.demarcation_code,
          info: muni,
        };
      });

      this.$muniChooser = this.$('.muni-chooser').select2({
        data: munis,
        placeholder: "Find a municipality",
        allowClear: true,
        templateResult: formatMuni,
      })
        .on('select2:select', _.bind(this.muniSelected, this));
    },

    renderYears: function() {
      var $chooser = this.$('.year-chooser');

      for (var i = 0; i < this.years.length; i++) {
        var year = this.years[i];
        $chooser.append($('<li><label><input type="radio" name="year" value="' + year + '"> ' + year + '</label></li>'));
      }
    },

    muniSelected: function(e) {
      var munis = this.filters.get('municipalities');
      var id = e.params.data.id;

      if (id && _.indexOf(munis, id) === -1) {
        // duplicate the array
        munis = munis.concat([id]);
        this.filters.set('municipalities', _.sortBy(munis, function(m) { return municipalities[m].name; }));
        this.filters.trigger('change');
      }

      this.$muniChooser.val(null).trigger('change');
    },

    muniRemoved: function(e) {
      e.preventDefault();
      var id = $(e.target).closest('li').data('id');
      this.filters.set('municipalities', _.without(this.filters.get('municipalities'), id));
    },

    yearChanged: function(e) {
      this.filters.set('year', Number.parseInt(this.$('input[name=year]:checked').val()));
    },
  });


  /** The data table portion of the page.
   */
  var TableView = Backbone.View.extend({
    el: '#table-view',

    events: {
      'click .scale': 'changeScale',
      'mouseover .table-display tr': 'rowOver',
      'mouseout .table-display tr': 'rowOut',
      'click .table-display tr': 'rowClick',
    },

    initialize: function(opts) {
      this.format = d3_format
        .formatLocale({decimal: ".", thousands: " ", grouping: [3], currency: "R"})
        .format(",d");
      this.scale = 3;

      this.filters = opts.filters;
      this.filters.on('change', this.render, this);
      this.filters.on('change', this.update, this);

      this.state = opts.state;
      this.state.on('change', this.loadState, this);

      this.cells = opts.cells;
      this.cells.on('change', this.render, this);

      this.preload();
      this.loadState();
    },

    loadState: function() {
      // load state from browser history
      this.scale = this.state.get('scale');
      if (!_.contains([0, 3, 6], this.scale)) this.scale = 3;
      this.render();
    },

    saveState: function() {
      // save global state to browser history
      this.state.set({
        scale: this.scale,
      });
    },

    preload: function() {
      var self = this;

      // TODO does this work for all cubes?
      spinnerStart();
      $.get(MUNI_DATA_API + '/cubes/' + CUBE_NAME + '/members/item', function(data) {
        // we only care about items that have a label
        self.rowHeadings = _.select(data.data, function(d) { return d['item.label']; });
        self.renderRowHeadings();
        self.render();
      }).always(spinnerStop);
    },

    changeScale: function() {
      this.scale = Number.parseInt(this.$('.scale input:checked').attr('value'));
      this.saveState();
      this.render();
    },

    /**
     * Update the data!
     */
    update: function() {
      var self = this;
      var url = MUNI_DATA_API + '/cubes/' + CUBE_NAME + '/aggregate?';

      if (this.filters.get('municipalities').length === 0) {
        this.cells.set({items: [], meta: {}});
        return;
      }

      var cells = [];
      this.cells.set('items', cells);

      var parts = {
        aggregates: cube.aggregates,
        drilldown: cube.drilldown,
        order: cube.order,
        cut: ['financial_period.period:' + self.filters.get('year'),
              // TODO: work out possibilities here based on year
              // eg: https://data.municipalmoney.org.za/api/cubes/incexp/members/amount_type?cut=financial_period:2015
              'amount_type.code:AUDA'],
      };
      var cut = parts.cut;

      _.each(this.filters.get('municipalities'), function(muni) {
        // duplicate this, we're going to change it
        parts.cut = cut.slice();

        // TODO: do this in bulk, rather than 1-by-1
        parts.cut.push('demarcation.code:"' + muni + '"');

        // TODO: paginate

        var url = self.makeUrl(parts);
        console.log(url);

        spinnerStart();
        $.get(url, function(data) {
          self.cells.set('items', self.cells.get('items').concat(data.cells));
        }).always(spinnerStop);
      });
    },

    makeUrl: function(parts) {
      var url = MUNI_DATA_API + '/cubes/' + CUBE_NAME + '/aggregate?';
      return url + _.map(parts, function(value, key) {
        if (_.isArray(value)) value = value.join('|');
        return key + '=' + encodeURIComponent(value);
      }).join('&');
    },

    render: function() {
      if (this.rowHeadings && municipalities) {
        this.renderColHeadings();
        this.renderValues();
      }

      var scale = this.scale.toString();
      this.$('input[name=scale]').prop('checked', function() {
        return $(this).val() == scale;
      });
    },

    renderRowHeadings: function() {
      // render row headings table
      var table = this.$('.row-headings')[0];

      for (var i = 0; i < (cube.aggregates.length > 1 ? 2 : 1); i++) {
        var spacer = $('<th>').html('&nbsp;').addClass('spacer');
        table.insertRow().appendChild(spacer[0]);
      }

      for (i = 0; i < this.rowHeadings.length; i++) {
        var item = this.rowHeadings[i];
        var tr = table.insertRow();
        var td;

        $(tr).addClass('item-' + item['item.return_form_structure']);
        
        td = tr.insertCell();
        td.innerText = item['item.code'];
        td = tr.insertCell();
        td.innerText = item['item.label'];
        td.setAttribute('title', item['item.label']);
      }
    },

    renderColHeadings: function() {
      var table = this.$('.values').empty()[0];

      // municipality headings
      var tr = table.insertRow();
      var munis = this.filters.get('municipalities');
      for (var i = 0; i < munis.length; i++) {
        var muni = municipalities[munis[i]];
        var th = document.createElement('th');
        th.innerText = muni.name;
        th.setAttribute('colspan', cube.aggregates.length);
        th.setAttribute('title', muni.demarcation_code);
        tr.appendChild(th);
      }

      // aggregate headings
      if (cube.aggregates.length > 1) {
        tr = table.insertRow();

        for (i = 0; i < munis.length; i++) {
          _.each(cube.model.measures, function(measure) {
            var th = document.createElement('th');
            th.innerText = measure.label;
            tr.appendChild(th);
          });
        }
      }
    },

    renderValues: function() {
      var table = this.$('.values')[0];
      var cells = this.cells.get('items');
      var munis = this.filters.get('municipalities');
      var scale = Math.pow(10, Number.parseInt(this.scale));
      // highlightable items as a set of codes
      var highlights = _.inject(this.state.get('items') || [], function(s, i) { s[i] = i; return s; }, {});
      // row indexes to highlight
      var toHighlight = [];
      var self = this;

      // group by code then municipality
      cells = _.groupBy(cells, 'item.code');
      _.each(cells, function(items, code) {
        cells[code] = _.indexBy(items, 'demarcation.code');
      });

      // values
      if (!_.isEmpty(cells)) {
        for (var i = 0; i < this.rowHeadings.length; i++) {
          var row = this.rowHeadings[i];
          var tr = table.insertRow();
          $(tr).addClass('item-' + row['item.return_form_structure']);

          // highlight?
          if (highlights[row['item.code']]) toHighlight.push(table.rows.length-1);

          for (var j = 0; j < munis.length; j++) {
            var muni = municipalities[munis[j]];
            var cell = cells[row['item.code']];

            if (cell) cell = cell[muni.demarcation_code];

            for (var a = 0; a < cube.aggregates.length; a++) {
              var v = (cell ? cell[cube.aggregates[a]] : null);
              tr.insertCell().innerText = v ? self.format(v / scale) : "-";
            }
          }
        }
      }

      // highlighted rows
      for (var h = 0; h < toHighlight.length; h++) {
        var ix = toHighlight[h];
        this.$('table.row-headings tr:eq(' + ix + '), table.values tr:eq(' + ix + ')')
          .addClass('toggled');
      }
    },

    rowClick: function(e) {
      var ix = $(e.currentTarget).index();
      this.$('table.row-headings tr:eq(' + ix + '), table.values tr:eq(' + ix + ')')
        .toggleClass('toggled');
    },

    rowOver: function(e) {
      var ix = $(e.currentTarget).index();
      this.$('table.row-headings tr:eq(' + ix + '), table.values tr:eq(' + ix + ')')
        .addClass('hover');
    },

    rowOut: function(e) {
      var ix = $(e.currentTarget).index();
      this.$('table.row-headings tr:eq(' + ix + '), table.values tr:eq(' + ix + ')')
        .removeClass('hover');
    },
  });


  /** Overall table view on this page
   */
  var MainView = Backbone.View.extend({
    initialize: function() {
      this.filters = new Filters();
      this.cells = new Cells();

      this.state = new State();
      this.loadState();
      this.state.on('change', this.saveState, this);

      this.filterView = new FilterView({filters: this.filters, state: this.state});
      this.tableView = new TableView({filters: this.filters, cells: this.cells, state: this.state});
    },

    saveState: function() {
      if (history.replaceState) {
        var state = this.state.toJSON();
        var url = {
          year: state.year,
          municipalities: state.municipalities.join(','),
          scale: state.scale,
        };

        // make the query string url
        url = _.compact(_.map(url, function(val, key) {
          if (!_.isNaN(val) && (_.isNumber(val) || !_.isEmpty(val))) return key + '=' + encodeURIComponent(val);
        })).join('&');

        history.replaceState({}, document.title, url ? ('?' + url) : "");
      }
    },

    loadState: function() {
      // parse query string
      var params = {};
      var parts = document.location.search.substring(1).split("&");
      for (var i = 0; i < parts.length; i++) {
        var p = parts[i].split('=');
        params[p[0]] = decodeURIComponent(p[1]);
      }

      this.state.set({
        municipalities: (params.municipalities || "").split(","),
        year: Number.parseInt(params.year) || null,
        scale: Number.parseInt(params.scale),
        // highlighted item codes
        items: (params.items || "").split(","),
      });
    },
  });

  exports.view = new MainView();
})(window);
