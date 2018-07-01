
# Build (optional) third_party tools
mkdir -p third_party

##  ffmpegthumbnailer
cd third_party
git clone --depth=1 https://github.com/dirkvdb/ffmpegthumbnailer.git
cd ffmpegthumbnailer
mkdir -p build
cd build
cmake -DCMAKE_BUILD_TYPE=Release ..
cmake --build .
cd ../..

## Done building third_party tools
cd ..

# Build photo-selector
mkdir -p build
cd build
cmake -DCMAKE_BUILD_TYPE=Release ..
cmake --build .
