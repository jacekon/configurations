#!/usr/bin/swift

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
    
    // Load the image natively
    guard let imageSource = CGImageSourceCreateWithURL(file as CFURL, nil),
          let cgImage = CGImageSourceCreateImageAtIndex(imageSource, 0, nil) else {
        continue
    }
    
    // Set up Apple's text recognition request
    let request = VNRecognizeTextRequest { (request, error) in
        guard let observations = request.results as? [VNRecognizedTextObservation] else { return }
        
        // Threshold: If an image has more than 12 detected lines of text, it's likely a document
        if observations.count > 12 {
            print("Document detected: \(file.lastPathComponent) (\(observations.count) lines of text)")
            let destination = destURL.appendingPathComponent(file.lastPathComponent)
            try? fm.moveItem(at: file, to: destination)
        }
    }
    
    // Use .fast for speed, change to .accurate if you want it to read tiny/blurry text
    request.recognitionLevel = .fast 
    
    let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
    try? handler.perform([request])
}
