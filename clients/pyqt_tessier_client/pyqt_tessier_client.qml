import QtQuick 1.1

Rectangle {
    id: tessierec
    width: 200
    height: 300
    Text {
        id: jemoeder
        text: "BOOOOOOOOm start ze measure"
    }
    MouseArea {
		anchors.fill: parent
		onClicked: { controller.startmeasure()}
		}
}
