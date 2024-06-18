from helper import *

data = get_df()
rangeHeatmaps_array = data['rangeHeatmap']
velocities_array = data['velocity']
L_R_array = data['L_R']
X_train, X_test, y_train, y_test = train_test_split(rangeHeatmaps_array, velocities_array, test_size=0.2, random_state=42)
# train_X = X_train.reshape(X_train.shape[0],28,28,1)
X_train = np.expand_dims(X_train, axis = -1)
print("********X SHAPE:", X_train.shape)
model = get_model()
# model = train(model, X_train, y_train, L_R_array, epochs=500)
model = traincnn(model, X_train, y_train, epochs=500)
test_result = test(model, X_test, y_test)