console.log("main.js loaded");
// import * as THREE from 'three';

const video = document.getElementById('video-stream');
const statusDiv = document.getElementById('status');
const canvas = document.getElementById('three-canvas');

// Set up canvas for video rendering
// const ctx = canvas.getContext('2d');
// canvas.width = 640;
// canvas.height = 480;

// Three.js setup
let renderer, scene, camera, shoeModel, light;
let modelLoaded = false;

function initThree() {

    console.log("model loading ------");
    renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true });
    renderer.setSize(640, 480);
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(45, 640/480, 0.1, 1000);
    camera.position.set(0, 0, 2);
    light = new THREE.DirectionalLight(0xffffff, 1);
    light.position.set(0, 1, 2);
    scene.add(light);
    scene.add(new THREE.AmbientLight(0xffffff, 0.5));

    // Load OBJ model
    const loader = new THREE.GLTFLoader();
    loader.load(
        'wood_shoes.glb',
        function (obj) {
            console.log("obj", obj);
            shoeModel = obj;
            shoeModel.scale.set(0.2, 0.2, 0.2); // Adjust as needed
            scene.add(shoeModel);
            modelLoaded = true;
        },
        undefined,
        function (err) {
            console.error('Error loading OBJ:', err);
            // Fallback: Try loading GLTF model
            // if (typeof THREE.GLTFLoader === 'undefined') {
            //     const gltfScript = document.createElement('script');
            //     gltfScript.src = 'https://cdn.jsdelivr.net/npm/three@0.152.2/examples/js/loaders/GLTFLoader.js';
            //     gltfScript.onload = loadGLTFModel;
            //     document.head.appendChild(gltfScript);
            // } else {
            //     loadGLTFModel();
            // }
        }
    );
}

function loadGLTFModel() {
    const gltfLoader = new THREE.GLTFLoader();
    // Adjust the path to your GLTF model as needed
    console.log("gltf loading ------");
    gltfLoader.load(
        'wood_shoes.glb',
        function (gltf) {
            shoeModel = gltf.scene;
            shoeModel.scale.set(0.2, 0.2, 0.2); // Adjust as needed
            scene.add(shoeModel);
            modelLoaded = true;
            console.log('GLTF model loaded as fallback');
        },
        undefined,
        function (error) {
            console.error('Error loading GLTF model:', error);
        }
    );
}

// Load OBJLoader
// if (typeof THREE.OBJLoader === 'undefined') {
//     const script = document.createElement('script');
//     script.src = 'https://cdn.jsdelivr.net/npm/three@0.152.2/examples/js/loaders/OBJLoader.js';
//     script.onload = initThree;
//     document.head.appendChild(script);
// } else {
//     initThree();
// }

const socket = io('http://localhost:5000');
console.log("Socket.IO client initialized");

// Catch-all event logger
socket.onAny((event, ...args) => {
    console.log("[Socket.IO] Event received:", event, args);
});

socket.on('connect', () => {
    console.log("Connected to backend!");
    statusDiv.textContent = 'Connected to backend!';
    socket.emit('start_stream');
});

socket.on('disconnect', () => {
    console.log("Disconnected from backend.");
    statusDiv.textContent = 'Disconnected from backend.';
});

socket.on('stream_started', () => {
    console.log("Stream started!");
    statusDiv.textContent = 'Stream started!';
});

function applyTransformToModel(model, transform) {
    const m = new THREE.Matrix4();
    m.set(
        transform[0][0], transform[0][1], transform[0][2], transform[0][3],
        transform[1][0], transform[1][1], transform[1][2], transform[1][3],
        transform[2][0], transform[2][1], transform[2][2], transform[2][3],
        transform[3][0], transform[3][1], transform[3][2], transform[3][3]
    );
    model.matrixAutoUpdate = false;
    model.matrix.copy(m);
}

socket.on('frame', (data) => {
    console.log("Frame received", data);
    // Draw video frame
    // const img = new window.Image();
    // img.onload = function() {
    //     ctx.clearRect(0, 0, canvas.width, canvas.height);
    //     ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    // };
    // img.src = 'data:image/jpeg;base64,' + data.frame;

    // Map 3D shoe model
    if (modelLoaded && data.foot_data && data.foot_data.length > 0) {
        const foot = data.foot_data[0];
        let transform = foot.transform;

        // If axes are flipped, adjust here (example: swap Y and Z)
        for (let i = 0; i < 3; i++) {
            [transform[i][1], transform[i][2]] = [transform[i][2], transform[i][1]];
        }
        console.log("transform", transform);
        applyTransformToModel(shoeModel, transform);
        renderer.render(scene, camera);
    }

    if (data.foot_data && data.foot_data.length > 0) {
        let html = '';
        data.foot_data.forEach((foot, i) => {
            html += `<div>Foot ${i} (${foot.side}):<br>3D transform: <pre>${JSON.stringify(foot.transform, null, 2)}</pre></div>`;
        });
        statusDiv.innerHTML = html;
    } else {
        statusDiv.textContent = 'No foot detected';
    }
});

// socket.on('frame', (data) => {
//     // ... draw video frame ...
//     console.log("Frame trying ---- ", data);
//     if (modelLoaded && data.foot_data && data.foot_data.length > 0) {
//         const foot = data.foot_data[0];
//         let transform = foot.transform;
//         applyTransformToModel(shoeModel, transform);
//         renderer.render(scene, camera);
//     }
//     // ... status update ...
//     console.log("Frame received", data);
// });

window.addEventListener('beforeunload', () => {
    socket.emit('stop_stream');
    socket.close();
}); 


initThree();