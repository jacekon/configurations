#!/usr/bin/swift
// Moves images that contain dense text into Document_Pics/ using Apple's Vision framework.
//
// Runs as a standalone Swift script — no Python or external tools needed.
// Uses VNRecognizeTextRequest (same engine as Live Text in macOS/iOS).
//
// Trigger: >12 text observation lines detected in the image.
// "Observations" are regions Vision identified as containing text.
// Dense documents (invoices, screenshots, articles) produce many regions;
// photos with incidental signage produce few.
//
// recognitionLevel = .fast — sufficient for clear, high-res screenshots.
// Change to .accurate if you need to handle blurry or small-font images.
//
// Usage:
//   swift filter_docs_native.swift [/path/to/folder]
//   (defaults to current directory if no path is given)

import Foundation
import Vision
import ImageIO

let arguments = CommandLine.arguments
let sourcePath = arguments.count > 1 ? arguments[1] : FileManager.default.currentDirectoryPath
let sourceURL = URL(fileURLWithPath: sourcePath)
let destURL = sourceURL.appendingPathComponent("Document_Pics")

let fm = FileManager.default
try? fm.createDirectory(at: destURL, withIntermediateDirectories: true)

guard let files = try? fm.contentsOfDirectory(at: sourceURL, includingPropertiesForKeys: nil) else {
    print("Could not read directory: \(sourcePath)")
    exit(1)
}

let imageExtensions = ["jpg", "jpeg", "png", "heic"]

for file in files {
    if !imageExtensions.contains(file.pathExtension.lowercased()) { continue }

    guard let imageSource = CGImageSourceCreateWithURL(file as CFURL, nil),
          let cgImage = CGImageSourceCreateImageAtIndex(imageSource, 0, nil) else {
        continue
    }

    let request = VNRecognizeTextRequest { (request, error) in
        guard let observations = request.results as? [VNRecognizedTextObservation] else { return }

        // Each observation is a distinct block of text Vision found.
        // >12 blocks reliably separates multi-paragraph documents from
        // photos with a sign or label.
        if observations.count > 12 {
            print("Document detected: \(file.lastPathComponent) (\(observations.count) lines)")
            let destination = destURL.appendingPathComponent(file.lastPathComponent)
            try? fm.moveItem(at: file, to: destination)
        }
    }

    request.recognitionLevel = .fast
    let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
    try? handler.perform([request])
}
