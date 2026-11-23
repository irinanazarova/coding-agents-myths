<issue>
Class Sphere is missing property isSphere
### Description

Box3 has this.isBox3 = true;
Sphere does not have this.isSphere;

### Reproduction steps

I need it for 
if(collider.isSphere)

### Code

a = new Sphere()
if(a.isSphere){ debugger }

### Live example

no example

### Screenshots

_No response_

### Version

r159

### Device

_No response_

### Browser

_No response_

### OS

_No response_

</issue>

The repository for this issue is checked out at /testbed, with its dependencies installed. Make the minimal changes to non-test files in /testbed to resolve the issue. Hidden tests will check your fix, so don't modify existing tests. When you're done, stop.
