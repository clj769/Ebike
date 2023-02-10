//The maximum zoom level to cluster data point data on the map.
var maxClusterZoomLevel = 1;

//The URL to the store location data.
var storeLocationDataUrl = "static/exvehicles.txt";

//The URL to the icon image.
var iconImageUrl = "static/img/iconlayer.png";
var iconEbike = "static/img/Ebike.png";
var iconEscooter = "static/img/Escooter.png";

var map,
    popup,
    datasource,
    datasourceEbike,
    datasourceEscooter,
    iconLayer,
    centerMarker,
    searchURL;

var second = 0;
var clock;
var timerUse = 0;

function loadStoreData() {
  //Download the store location data.
  fetch(storeLocationDataUrl)
      .then((response) => response.text())
      .then(function (text) {
        //Parse the Tab delimited file data into GeoJSON features.
        var featuresEbike = [];
        var featuresEscooter = [];
        var features = [];

        //Split the lines of the file.
        var lines = text.split("\n");

        //Grab the header row.
        var row = lines[0].split(",");

        //Parse the header row and index each column, so that when our code for parsing each row is easier to follow.
        var header = {};
        var numColumns = row.length;
        var i;

        for (i = 0; i < row.length; i++) {
          header[row[i]] = i;
        }

        //Skip the header row and then parse each row into a GeoJSON feature.
        for (i = 1; i < lines.length; i++) {
          row = lines[i].split(",");

          //Ensure that the row has the right number of columns.
          if (row.length >= numColumns && row[header["Vehicle_Type"]] == "bike" && row[header["Vehicle_Operational_Status"]] == "available"  && row[header["Vehicle_Defect_Status"]] == "non") {
            featuresEbike.push(
                new atlas.data.Feature(
                    new atlas.data.Point([
                      parseFloat(row[header["Vehicle_Longitude"]]),
                      parseFloat(row[header["Vehicle_Latitude"]]),
                    ]),
                    {
                      ID: row[header["Vehicle_ID"]],
                      Type: row[header["Vehicle_Type"]],
                      Battery: row[header["Vehicle_Battery"]],
                    }
                )
            );
          }

          if (row.length >= numColumns && row[header["Vehicle_Type"]] == "scooter"&& row[header["Vehicle_Operational_Status"]] == "available"  && row[header["Vehicle_Defect_Status"]] == "non") {
            featuresEscooter.push(
                new atlas.data.Feature(
                    new atlas.data.Point([
                      parseFloat(row[header["Vehicle_Longitude"]]),
                      parseFloat(row[header["Vehicle_Latitude"]]),
                    ]),
                    {
                      ID: row[header["Vehicle_ID"]],
                      Type: row[header["Vehicle_Type"]],
                      Battery: row[header["Vehicle_Battery"]],
                    }
                )
            );
          }

          if (row.length >= numColumns&& row[header["Vehicle_Operational_Status"]] == "available"  && row[header["Vehicle_Defect_Status"]] == "non") {
            features.push(
                new atlas.data.Feature(
                    new atlas.data.Point([
                      parseFloat(row[header["Vehicle_Longitude"]]),
                      parseFloat(row[header["Vehicle_Latitude"]]),
                    ]),
                    {
                      ID: row[header["Vehicle_ID"]],
                      Type: row[header["Vehicle_Type"]],
                      Battery: row[header["Vehicle_Battery"]],
                    }
                )
            );
          }
        }

        //Add the features to the data source.
        datasourceEbike.add(featuresEbike);
        datasourceEscooter.add(featuresEscooter);
        datasource.add(features);

        //Initially update the list items.
        updateListItems();
      });
}

// Add starttimer and stoptimer function
var count = 0;
var timer = null;
function initialize(properties) {

  //Initialize a map instance.
  map = new atlas.Map("myMap", {
    center: [-4.28922, 55.87189],
    zoom: 14,
    view: "Auto",

    //Add authentication details for connecting to Azure Maps.
    authOptions: {
      authType: "subscriptionKey",
      subscriptionKey: "oJQgJqDLYMzKdkgz9dzAzz9A4DdikmfzB4AUoeaB5M8",
    },
  });

  //Create a popup but leave it closed so we can update it and display it later.
  popup = new atlas.Popup();

  //Use MapControlCredential to share authentication between a map control and the service module.
  var pipeline = atlas.service.MapsURL.newPipeline(
      new atlas.service.MapControlCredential(map)
  );

  //Create an instance of the SearchURL client.
  searchURL = new atlas.service.SearchURL(pipeline);

  //If the user presses the search button, geocode the value they passed in.

  //If the user presses enter in the search textbox, perform a search.

  //If the user presses the My Location button, use the geolocation API to get the users location and center/zoom the map to that location.

  //Wait until the map resources are ready.
  map.events.add("ready", function () {
    //Add the zoom control to the map.
    map.controls.add(new atlas.control.ZoomControl(), {
      position: "top-right",
    });

    //Add an HTML marker to the map to indicate the center used for searching.
    centerMarker = new atlas.HtmlMarker({
      htmlContent: '<div class="mapCenterIcon"></div>',
      position: map.getCamera().center,
    });

    map.markers.add(centerMarker);

    //Create a data source and add it to the map and enable clustering.
    datasourceEbike = new atlas.source.DataSource(null, {
      cluster: false,
      clusterMaxZoom: maxClusterZoomLevel - 1,
    });
    datasourceEscooter = new atlas.source.DataSource(null, {
      cluster: false,
      clusterMaxZoom: maxClusterZoomLevel - 1,
    });
    datasource = new atlas.source.DataSource();

    map.sources.add(datasourceEbike);
    map.sources.add(datasourceEscooter);
    map.sources.add(datasource);

    //Load all the store data now that the data source has been defined.
    loadStoreData();

    //Create a bubble layer for rendering clustered data points.
    var clusterBubbleLayer = new atlas.layer.BubbleLayer(
        datasourceEbike,
        null,
        {
          radius: 12,
          color: "#007faa",
          strokeColor: "white",
          strokeWidth: 2,
          filter: ["has", "point_count"], //Only render data points which have a point_count property, which clusters do.
        }
    );

    //Create a symbol layer to render the count of locations in a cluster.
    var clusterLabelLayer = new atlas.layer.SymbolLayer(datasourceEbike, null, {
      iconOptions: {
        image: "none", //Hide the icon image.
      },
      textOptions: {
        textField: ["get", "point_count_abbreviated"],
        size: 12,
        font: ["StandardFont-Bold"],
        offset: [0, 0.4],
        color: "white",
      },
    });

    //map.layers.add([clusterBubbleLayer, clusterLabelLayer]);

    //Load a custom image icon into the map resources.

    map.imageSprite.add("icon", iconImageUrl).then(function () {
      iconLayer = new atlas.layer.SymbolLayer(datasource, null, {
        iconOptions: {
          //Pass in the id of the custom icon that was loaded into the map resources.
          image: "icon",

          //Optionally scale the size of the icon.
          font: ["SegoeUi-Bold"],

          //Anchor the center of the icon image to the coordinate.
          anchor: "center",

          //Allow the icons to overlap.
          allowOverlap: true,
        },
        filter: ["!", ["has", "point_count"]], //Filter out clustered points from this layer.
      });

      map.layers.add(iconLayer);
    });

    map.imageSprite.add("ebikeIcon", iconEbike).then(function () {
      //Create a layer to render a coffe cup symbol above each bubble for an individual location.
      iconLayerebike = new atlas.layer.SymbolLayer(datasourceEbike, null, {
        iconOptions: {
          //Pass in the id of the custom icon that was loaded into the map resources.
          image: "ebikeIcon",

          //Optionally scale the size of the icon.
          font: ["SegoeUi-Bold"],

          //Anchor the center of the icon image to the coordinate.
          anchor: "center",

          //Allow the icons to overlap.
          allowOverlap: true,
        },
        filter: ["!", ["has", "point_count"]], //Filter out clustered points from this layer.
      });

      map.layers.add(iconLayerebike);

      //When the mouse is over the cluster and icon layers, change the cursor to be a pointer.
      map.events.add(
          "mouseover",
          [clusterBubbleLayer, iconLayerebike],
          function () {
            map.getCanvasContainer().style.cursor = "pointer";
          }
      );

      //When the mouse leaves the item on the cluster and icon layers, change the cursor back to the default which is grab.


      //Add a click event to the cluster layer. When someone clicks on a cluster, zoom into it by 2 levels.
      map.events.add("click", clusterBubbleLayer, function (e) {
        map.setCamera({
          center: e.position,
          zoom: map.getCamera().zoom + 2,
        });
      });

      //Add a click event to the icon layer and show the shape that was clicked.

      map.events.add("mouseover", iconLayerebike, function (e) {
        showPopup(e.shapes[0]);
      });

      //Add an event to monitor when the map has finished moving.
      map.events.add("render", function () {
        //Give the map a chance to move and render data before updating the list.
        updateListItems();
      });

      map.events.add("click", iconLayerebike, function () {
        console.log("iconLayerebike");
        clearInterval(timer);
        count = 0;
        startTimer1();
        if(status){
          alert("You have already rented a vehicle!");
        }else{
           window.open('rent','_self');
        }

      });
    });

    map.imageSprite.add("escooterIcon", iconEscooter).then(function () {
      //Create a layer to render a coffe cup symbol above each bubble for an individual location.
      iconLayerscooter = new atlas.layer.SymbolLayer(datasourceEscooter, null, {
        iconOptions: {
          //Pass in the id of the custom icon that was loaded into the map resources.
          image: "escooterIcon",

          //Optionally scale the size of the icon.
          font: ["SegoeUi-Bold"],

          //Anchor the center of the icon image to the coordinate.
          anchor: "center",

          //Allow the icons to overlap.
          allowOverlap: true,
        },
        filter: ["!", ["has", "point_count"]], //Filter out clustered points from this layer.
      });

      map.layers.add(iconLayerscooter);

      //When the mouse is over the cluster and icon layers, change the cursor to be a pointer.
      map.events.add(
          "mouseover",
          [clusterBubbleLayer, iconLayerscooter],
          function () {
            map.getCanvasContainer().style.cursor = "pointer";
          }
      );

      //Add a click event to the icon layer and show the shape that was clicked.
      map.events.add("mouseover", iconLayerscooter, function (e) {
        showPopup(e.shapes[0]);
      });

      map.events.add("click", iconLayerscooter, function () {
      if(status){
          alert("You have already rented a vehicle!");
        }else{
           window.open('rent','_self');
        }

      });

      //Add an event to monitor when the map has finished moving.
      map.events.add("render", function () {
        //Give the map a chance to move and render data before updating the list.
        updateListItems();
      });

      map.events.add("click", iconLayerscooter, function () {
        console.log("iconEscooter");
        clearInterval(timer);
        count = 0;

        startTimer1();
      });
    });
  });
}
// User's startimer and counter
function startTimer1() {
  var second = document.getElementById("second");

  timer = setInterval(function () {
    count++;

    second.innerHTML = count;
  }, 1000);
}

function updateListItems() {
  //Hide the center marker.
  centerMarker.setOptions({
    visible: false,
  });

  //Get the current camera/view information for the map.
  var camera = map.getCamera();

  var listPanel = document.getElementById("listPanel");

  //Check to see if the user is zoomed out a lot. If they are, tell them to zoom in closer, perform a search or press the My Location button.
  if (camera.zoom < maxClusterZoomLevel) {
    //Close the popup as clusters may be displayed on the map.
    popup.close();

    listPanel.innerHTML =
        '<div class="statusMessage">Search for a location, zoom the map, or press the "My Location" button to see individual locations.</div>';
  } else {
    //Update the location of the centerMarker.
    centerMarker.setOptions({
      position: camera.center,
      visible: true,
    });

    //List the ten closest locations in the side panel.
    var html = [],
        properties;

    var data = map.layers.getRenderedShapes(map.getCamera().bounds, [
      iconLayer,
    ]);

    navigator.geolocation.getCurrentPosition(
        function (position) {
          var userP = position;
          //Convert the geolocation API position into a longitude/latitude position value the map can understand and center the map over it.
          map.setCamera({
            center: [position.coords.longitude, position.coords.latitude],
          });
        },
        function (error) {
          //If an error occurs when trying to access the users position information, display an error message.
          switch (error.code) {
            case error.PERMISSION_DENIED:
              alert("User denied the request for Geolocation.");
              break;
            case error.POSITION_UNAVAILABLE:
              alert("Position information is unavailable.");
              break;
            case error.TIMEOUT:
              alert("The request to get user position timed out.");
              break;
            case error.UNKNOWN_ERROR:
              alert("An unknown error occurred.");
              break;
          }
        }
    );

    //Create an index of the distances of each shape.
    var distances = {};

    data.forEach(function (shape) {
      if (shape instanceof atlas.Shape) {
        //Calculate the distance from the center of the map to each shape and store in the index. Round to 2 decimals.
        distances[shape.getId()] =
            Math.round(
                atlas.math.getDistanceTo(
                    camera.center,
                    shape.getCoordinates(),
                    "miles"
                ) * 100
            ) / 100;
      }
    });

    //Sort the data by distance.
    data.sort(function (x, y) {
      return distances[x.getId()] - distances[y.getId()];
    });

    data.forEach(function (shape) {
      properties = shape.getProperties();

      html.push(
          '<div class="listItemcontent" onmouseenter="itemOver(\'',
          shape.getId(),
          '\')" >   <div class="listItem-title" >',
          properties["Type"],
          "</div>",

          getSOC(properties),
          "<br />",

          //Get the price.
          getPrice(properties),
          "<br />",

          //Get the distance of the shape.
          distances[shape.getId()],
          " miles away</div>"
      );
    });

    listPanel.innerHTML = html.join("");

    //Scroll to the top of the list panel incase the user has scrolled down.
    listPanel.scrollTop = 0;
  }
}

//This converts a time in 2400 format into an AM/PM time or noon/midnight string.

function getPrice(properties) {
  var type = properties["Type"];
  if (type == "bike") {
    return "Price: 2 Pounds/Hour";
  }

  if (type == "scooter") {
    return "Price: 1 Pound/Hour";
  }
}

function getSOC(properties) {
  var Battery = properties["Battery"];
  var ID = properties["ID"];
  return "Battery is " + Battery + "  ID is " + ID;
}

function getvID(properties) {
  var ID = properties["ID"];
  return ID;
}

function disp_prompt() {
  var name = prompt("input", "");
  if (name != null && name != "") {
    alert("your input:" + name);
  }

  const fsLibrary = require("fs");
  let data = name;
  fsLibrary.writeFile("newfile.txt", name, { flag: "a" }, (error) => {
    if (error) throw error;
  });
}

function resetTimer() {
  clearInterval(clock);
  second = 0;
  document.getElementById("timeValue").value = second + "秒";
}

function startTimer() {
  clock = setInterval(timer, 1000);
  timerUse = 1;
}

function stopTimer() {
  clearInterval(clock);
  document.getElementById("timeValue").value = second + "秒";
  timerUse = 0;
}
function timer() {
  second++;
  document.getElementById("timeValue").value = second + "秒";
}

//When a user clicks on a result in the side panel, look up the shape by its id value and show popup.
function itemOver(id) {
  //Get the shape from the data source using it's id.
  var shape = datasource.getShapeById(id);
  showPopup(shape);
}

function iconClick(id) {
  //Get the shape from the data source using it's id.
  var shape = datasource.getShapeById(id);
  //showPopup(shape);

  //Center the map over the shape on the map.
  var offset;

  console.log("sssss");

  if (timerUse == 0) {
    startTimer();
  } else {
    stopTimer();
  }

  //If the map is less than 700 pixels wide, then the layout is set for small screens.
  if (map.getCanvas().width < 700) {
    //When the map is small, offset the center of the map relative to the shape so that there is room for the popup to appear.
    offset = [0, -80];
  }
}

function showPopup(shape) {
  var properties = shape.getProperties();

  //Calculate the distance from the center of the map to the shape in miles, round to 2 decimals.
  var distance =
      Math.round(
          atlas.math.getDistanceTo(
              map.getCamera().center,
              shape.getCoordinates(),
              "miles"
          ) * 100
      ) / 100;

  localStorage.vID = getvID(properties);
  var html = ['<div class="storePopup">'];

  html.push(
      '<div class="popupTitle">',
      properties["Type"],
      '<div class="popupSubTitle">',

      '</div></div><div class="popupContent">',

      getSOC(properties),
      "<br/>",
      //Convert the closing time into a nicely formated time.
      getPrice(properties),

      //Add the distance information.
      "<br/>",
      distance,
      " miles away",
      "</a>"
  );

  html.push("</div></div>");

  //Update the content and position of the popup for the specified shape information.
  popup.setOptions({
    //Create a table from the properties in the feature.
    content: html.join(""),
    position: shape.getCoordinates(),
  });

  //Open the popup.
  popup.open(map);
}

//Creates an addressLine2 string consisting of City, Municipality, AdminDivision, and PostCode.

//Initialize the application when the page is loaded.
(window.onload = initialize), setMapToUserLocation, updateListItems();
